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


import inspect
import os
import re
import shutil
import time
from errno import ENOSYS
from grp import getgrnam
from pwd import getpwnam

from gitfs.fuse_compat import get_fuse_module, is_fuse3, FUSE, FuseOSError

from gitfs.cache import CachedIgnore, lru_cache
from gitfs.events import fetch, idle, shutting_down
from gitfs.log import log
from gitfs.repository import Repository


class Router:
    def __init__(
        self,
        remote_url,
        repo_path,
        mount_path,
        credentials,
        current_path="current",
        history_path="history",
        branch=None,
        user="root",
        group="root",
        **kwargs,
    ):
        """
        Clone repo from a remote into repo_path/<repo_name> and checkout to
        a specific branch.

        :param str remote_url: URL of the repository to clone
        :param str repo_path: Where are all the repos are cloned
        :param str branch: Branch to checkout after the
            clone. The default is to use the remote's default branch.

        """

        self.remote_url = remote_url
        self.repo_path = repo_path
        self.mount_path = mount_path
        self.current_path = current_path
        self.history_path = history_path
        self.branch = branch

        print("branch", branch)

        self.routes = []

        log.info(f"Cloning into {self.repo_path}")

        self.repo = Repository.clone(
            self.remote_url, self.repo_path, self.branch, credentials
        )
        log.info("Done cloning")

        self.repo.credentials = credentials

        submodules = os.path.join(self.repo_path, ".gitmodules")
        ignore = os.path.join(self.repo_path, ".gitignore")
        self.repo.ignore = CachedIgnore(
            submodules=submodules,
            ignore=ignore,
            exclude=kwargs["ignore_file"] or None,
            hard_ignore=kwargs["hard_ignore"],
        )

        self.uid = getpwnam(user).pw_uid
        self.gid = getgrnam(group).gr_gid

        self.commit_queue = kwargs["commit_queue"]
        self.mount_time = int(time.time())

        self.max_size = kwargs["max_size"]
        self.max_offset = kwargs["max_offset"]

        self.repo.commits.update()

        self.workers = []

    def init(self, path):
        for worker in self.workers:
            worker.start()

        log.debug("Done init")

    def init_with_config(self, conn, config):
        """Compatibility method for mfusepy - delegates to init"""
        return self.init("/")

    def destroy(self, path):
        log.debug("Stopping workers")
        shutting_down.set()
        fetch.set()

        for worker in self.workers:
            try:
                if hasattr(worker, "is_alive") and worker.is_alive():
                    worker.join()
            except RuntimeError as e:
                log.debug(f"Worker join failed: {e}")
        log.debug("Workers stopped")

        shutil.rmtree(self.repo_path)
        log.info("Successfully umounted %s", self.mount_path)

    def register(self, routes):
        for regex, view in routes:
            log.debug("Registering %s for %s", view, regex)
            self.routes.append({"regex": regex, "view": view})
        log.debug(f"Total {len(self.routes)} routes registered")

    def get_view(self, path):
        """
        Try to map a given path to it's specific view.

        If a match is found, a view object is created with the right regex
        groups(named or unnamed).

        :param str path: path to be matched
        :rtype: view object, relative path
        """

        # Normalize empty or None paths to root path for FUSE compatibility
        # This MUST happen before route matching
        original_path = path

        # Handle various forms of empty/invalid paths from FUSE
        if (
            not path
            or path == ""
            or path is None
            or path.strip() == ""  # whitespace-only paths
            or not path.isprintable()  # non-printable characters like \x07
            or len(path) == 1
            and ord(path) < 32
        ):  # single control characters
            log.debug(f"Router: normalizing invalid path {repr(path)} to '/'")
            path = "/"

        log.debug(f"Router get_view: original='{original_path}' normalized='{path}'")

        log.debug(f"Router: trying to match '{path}' against {len(self.routes)} routes")
        for route in self.routes:
            log.debug(f"Router: testing '{path}' against '{route['regex']}'")
            result = re.search(route["regex"], path)
            if result is None:
                continue

            groups = result.groups()
            relative_path = re.sub(route["regex"], "", path)
            relative_path = "/" if not relative_path else relative_path

            cache_key = result.group(0)
            log.debug("Router: Cache key for %s: %s", path, cache_key)

            view = lru_cache.get_if_exists(cache_key)
            if view is not None:
                log.debug("Router: Serving %s from cache", path)
                return view, relative_path

            kwargs = result.groupdict()

            # TODO: move all this to a nice config variable
            kwargs["repo"] = self.repo
            kwargs["ignore"] = self.repo.ignore
            kwargs["repo_path"] = self.repo_path
            kwargs["mount_path"] = self.mount_path
            kwargs["regex"] = route["regex"]
            kwargs["relative_path"] = relative_path
            kwargs["current_path"] = self.current_path
            kwargs["history_path"] = self.history_path
            kwargs["uid"] = self.uid
            kwargs["gid"] = self.gid
            kwargs["branch"] = self.branch
            kwargs["mount_time"] = self.mount_time
            kwargs["queue"] = self.commit_queue
            kwargs["max_size"] = self.max_size
            kwargs["max_offset"] = self.max_offset

            args = set(groups) - set(kwargs.values())
            view = route["view"](*args, **kwargs)

            # Debug: Log which view type is being used for each path
            log.debug(f"Router: Path '{path}' -> {view.__class__.__name__}")

            lru_cache[cache_key] = view
            log.debug("Router: Added %s to cache", path)

            return view, relative_path

        log.debug(
            f"Router: No route matched for path '{path}' (original: '{original_path}')"
        )
        log.debug(
            f"Router: Available routes: {[route['regex'] for route in self.routes]}"
        )
        raise ValueError(f"Found no view for '{path}' (original: '{original_path}')")

    def __call__(self, operation, *args):
        """
        Magic method which calls a specific method from a view.

        In Fuse API, almost each method receives a path argument. Based on that
        path we can route each call to a specific view. For example, if a
        method which has a path argument like `/current/dir1/dir2/file1` is
        called, we need to get the certain view that will know how to handle
        this path, instantiate it and then call our method on the newly created
        object.

        :param str operation: Method name to be called
        :param args: tuple containing the arguments to be transmitted to
            the method
        :rtype: function
        """

        if operation in ["destroy", "init"]:
            view = self
        else:
            path = args[0]
            # Normalize empty paths to root - this will be done again in get_view but log here for debugging
            if not path or path == "" or path is None:
                log.debug(
                    f"Router: __call__ received empty path for operation {operation}"
                )
            log.debug(f"Router: Operation {operation} with original path: '{path}'")
            view, relative_path = self.get_view(path)
            args = (relative_path,) + args[1:]

        log.debug(f"Call {operation} {view.__class__.__name__} with {args!r}")

        if not hasattr(view, operation):
            log.debug(f"No attribute {operation} on {view.__class__.__name__}")
            raise FuseOSError(ENOSYS)

        idle.clear()
        result = getattr(view, operation)(*args)
        idle.set()

        return result

    def _create_operation_method(self, operation_name):
        """Create a method that delegates to the router's __call__ method"""

        def operation_method(*args, **kwargs):
            return self.__call__(operation_name, *args, **kwargs)

        operation_method.__name__ = operation_name
        return operation_method

    def __getattr__(self, attr_name):
        """
        Handle dynamic method creation for FUSE operations.

        During FUSE initialization, this method will be called to get
        callable methods for supported operations.
        """

        # Base FUSE operations supported by all versions
        fuse_operations = {
            "access",
            "chmod",
            "chown",
            "create",
            "destroy",
            "fallocate",
            "fgetattr",
            "flush",
            "fsync",
            "fsyncdir",
            "ftruncate",
            "getattr",
            "getxattr",
            "init",
            "ioctl",
            "link",
            "listxattr",
            "mkdir",
            "mknod",
            "open",
            "opendir",
            "poll",
            "read",
            "readdir",
            "readlink",
            "release",
            "releasedir",
            "removexattr",
            "rename",
            "rmdir",
            "setxattr",
            "statfs",
            "symlink",
            "truncate",
            "unlink",
            "utimens",
            "write",
        }

        # Add FUSE3-specific operations if using FUSE3
        if is_fuse3():
            fuse3_operations = {
                "copy_file_range",
                "lseek",
                "init_with_config",
            }
            fuse_operations = fuse_operations | fuse3_operations

        # Operations we don't support at all
        excluded_operations = {
            "bmap",
            "lock",
            "flock",
            "read_buf",
            "write_buf",
        }

        supported_operations = fuse_operations - excluded_operations

        # For excluded operations, return False to indicate they're not supported
        if attr_name in excluded_operations:
            return False

        if attr_name not in supported_operations:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{attr_name}'"
            )

        # Create and cache the method to avoid recreating it repeatedly
        method = self._create_operation_method(attr_name)
        setattr(self, attr_name, method)
        return method
