# Copyright 2014-2016 Presslabs SRL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import errno
import os
import re

from fuse import FuseOSError

from gitfs.events import writers
from gitfs.lfs import LFSPointer
from gitfs.log import log
from gitfs.utils.decorators.not_in import not_in
from gitfs.utils.decorators.write_operation import write_operation

from .passthrough import STATS, PassthroughView


class CurrentView(PassthroughView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dirty = {}

        self.current_path = kwargs.get("current_path", "current")

    @write_operation
    @not_in("ignore", check=["old", "new"])
    def rename(self, old, new):
        new = re.sub(self.regex, "", new)
        result = super().rename(old, new)

        message = f"Rename {old} to {new}"
        self._stage(**{"remove": os.path.split(old)[1], "add": new, "message": message})

        log.debug("CurrentView: Renamed %s to %s", old, new)
        return result

    @write_operation
    @not_in("ignore", check=["target"])
    def symlink(self, name, target):
        result = os.symlink(target, self.repo._full_path(name))

        message = f"Create symlink to {target} for {name}"
        self._stage(add=name, message=message)

        log.debug("CurrentView: Created symlink to %s from %s", name, target)
        return result

    @write_operation
    @not_in("ignore", check=["target"])
    def link(self, name, target):
        if target.startswith(f"/{self.current_path}/"):
            target = target.replace(f"/{self.current_path}/", "/")

        result = super().link(target, name)

        message = f"Create link to {target} for {name}"
        self._stage(add=name, message=message)

        log.debug("CurrentView: Created link to %s from %s", name, target)
        return result

    def readlink(self, path):
        log.debug("CurrentView: Read link %s", path)
        return os.readlink(self.repo._full_path(path))

    def getattr(self, path, fh=None):
        full_path = self.repo._full_path(path)
        status = os.lstat(full_path)

        attrs = {key: getattr(status, key) for key in STATS}
        attrs.update({"st_uid": self.uid, "st_gid": self.gid})

        log.debug("CurrentView: Get attributes %s for %s", str(attrs), path)
        return attrs

    @write_operation
    @not_in("ignore", check=["path"])
    def write(self, path, buf, offset, fh):
        """
        We don't like big big files, so we need to be really carefull
        with them. First we check for offset, then for size. If any of this
        is off limit, raise EFBIG error and delete the file.
        """

        if offset + len(buf) > self.max_size:
            raise FuseOSError(errno.EFBIG)

        result = super().write(path, buf, offset, fh)
        self.dirty[fh] = {"message": f"Update {path}", "stage": True}

        log.debug("CurrentView: Wrote %s to %s", len(buf), path)
        return result

    @write_operation
    @not_in("ignore", check=["path"])
    def mkdir(self, path, mode):
        result = super().mkdir(path, mode)

        keep_path = f"{path}/.keep"
        full_path = self.repo._full_path(keep_path)
        if not os.path.exists(keep_path):
            global writers
            fh = os.open(full_path, os.O_WRONLY | os.O_CREAT)
            writers += 1
            log.info("CurrentView: Open %s for write", full_path)

            super().chmod(keep_path, 0o644)

            self.dirty[fh] = {
                "message": f"Create the {path} directory",
                "stage": True,
            }

            self.release(keep_path, fh)

        log.debug("CurrentView: Created directory %s with mode %s", path, mode)

        return result

    def create(self, path, mode, fi=None):
        fh = self.open_for_write(path, os.O_WRONLY | os.O_CREAT)
        super().chmod(path, mode)

        self.dirty[fh] = {"message": f"Created {path}", "stage": True}

        log.debug("CurrentView: Created %s", path)
        return fh

    @write_operation
    @not_in("ignore", check=["path"])
    def chmod(self, path, mode):
        """
        Executes chmod on the file at os level and then it commits the change.
        """
        str_mode = (f"{mode:o}")[-4:]
        if str_mode not in ["0755", "0644"]:
            raise FuseOSError(errno.EINVAL)

        result = super().chmod(path, mode)

        if os.path.isdir(self.repo._full_path(path)):
            return result

        message = f"Chmod to {str_mode} on {path}"
        self._stage(add=path, message=message)

        log.debug("CurrentView: Change %s mode to %s", path, (f"0{mode:o}")[-4:])
        return result

    @write_operation
    @not_in("ignore", check=["path"])
    def fsync(self, path, fdatasync, fh):
        """
        Each time you fsync, a new commit and push are made
        """

        result = super().fsync(path, fdatasync, fh)

        message = f"Fsync {path}"
        self._stage(add=path, message=message)

        log.debug("CurrentView: Fsync %s", path)
        return result

    @write_operation
    @not_in("ignore", check=["path"])
    def open_for_write(self, path, flags):
        global writers
        fh = self.open_for_read(path, flags)
        writers += 1
        self.dirty[fh] = {"message": f"Opened {path} for write", "stage": False}

        log.debug("CurrentView: Open %s for write", path)
        return fh

    @write_operation
    @not_in("ignore", check=["path"])
    def lock(self, path, fip, cmd, lock):
        return super().lock(path, fip, cmd, lock)

    def open_for_read(self, path, flags):
        full_path = self.repo._full_path(path)
        log.info("CurrentView: Open %s for read", path)
        return os.open(full_path, flags)

    def open(self, path, flags):
        write_mode = flags & (os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT)
        if write_mode:
            return self.open_for_write(path, flags)
        return self.open_for_read(path, flags)

    def release(self, path, fh):
        """
        Check for path if something was written to. If so, commit and push
        the changed to upstream.
        """

        if fh in self.dirty:
            message = self.dirty[fh]["message"]
            should_stage = self.dirty[fh].get("stage", False)
            del self.dirty[fh]

            global writers
            writers -= 1
            if should_stage:
                log.debug("CurrentView: Staged %s for commit", path)
                self._stage(add=path, message=message)

        log.debug("CurrentView: Release %s", path)
        return os.close(fh)

    @write_operation
    @not_in("ignore", check=["path"])
    def rmdir(self, path):
        message = f"Delete the {path} directory"

        # Unlink all the files
        full_path = self.repo._full_path(path)
        for root, _dirs, files in os.walk(full_path):
            for _file in files:
                deleting_file = os.path.join(root, _file)
                if os.path.exists(deleting_file):
                    result = super().unlink(os.path.join(path, _file))
                    self._stage(remove=os.path.join(path, _file), message=message)

        # Delete the actual directory
        result = super().rmdir(f"{path}/")
        log.debug("CurrentView: %s", message)

        return result

    @write_operation
    @not_in("ignore", check=["path"])
    def unlink(self, path):
        result = super().unlink(path)

        message = f"Deleted {path}"
        self._stage(remove=path, message=message)

        log.debug("CurrentView: Deleted %s", path)
        return result

    def _stage(self, message, add=None, remove=None):
        non_empty = False

        if remove is not None:
            remove = self._sanitize(remove)
            if add is not None:
                add = self._sanitize(add)
                paths = self._get_files_from_path(add)
                if paths:
                    for path in paths:
                        path = path.replace(f"{add}/", f"{remove}/")
                        self.repo.index.remove(path)
                else:
                    self.repo.index.remove(remove)
            else:
                self.repo.index.remove(remove)
            non_empty = True

        if add is not None:
            add = self._sanitize(add)
            paths = self._get_files_from_path(add)
            if paths:
                for path in paths:
                    self._add_file_to_index(path)
            else:
                self._add_file_to_index(add)
            non_empty = True

        if non_empty:
            self.queue.commit(add=add, remove=remove, message=message)

    def _add_file_to_index(self, path):
        """Add a file to the git index, handling LFS when appropriate."""
        full_path = os.path.join(self.mount_path, path)
        
        # Check if LFS is enabled and this file should use LFS
        if (self.repo.lfs.is_lfs_enabled() and 
            os.path.exists(full_path) and 
            os.path.isfile(full_path)):
            
            file_size = os.path.getsize(full_path)
            
            # Check if this file should use LFS based on gitattributes
            if self.repo.lfs.should_use_lfs(path, file_size):
                log.info(f"Using LFS for large file: {path} ({file_size} bytes)")
                
                try:
                    # Read file content and create LFS pointer
                    with open(full_path, 'rb') as f:
                        content = f.read()
                    
                    # Create LFS pointer
                    pointer = LFSPointer.create_for_file(full_path)
                    
                    # Store the actual content in LFS object store
                    self.repo.lfs.store_lfs_object(content, pointer.oid)
                    
                    # Replace file content with pointer content temporarily
                    original_content = content
                    pointer_content = pointer.to_content()
                    
                    # Write pointer content to the file temporarily
                    with open(full_path, 'wb') as f:
                        f.write(pointer_content)
                    
                    # Add the pointer file to the index
                    self.repo.index.add(path)
                    
                    # Restore original content to the working directory
                    with open(full_path, 'wb') as f:
                        f.write(original_content)
                    
                    log.debug(f"Created LFS pointer for {path}: {pointer.oid}")
                    return
                    
                except Exception as e:
                    log.error(f"Failed to create LFS pointer for {path}: {e}")
                    # Fall back to regular git add
        
        # Regular file or LFS not enabled/applicable
        self.repo.index.add(path)

    def _get_files_from_path(self, path):
        paths = []

        full_path = self.repo._full_path(self._sanitize(path))
        workdir = self.repo._repo.workdir

        if os.path.isdir(full_path):
            for dirpath, _dirs, files in os.walk(full_path):
                for filename in files:
                    paths.append("{}/{}".format(dirpath.replace(workdir, ""), filename))
        return paths

    def _sanitize(self, path):
        if path is None:
            return path

        if path.startswith("/"):
            return path[1:]

        return path
