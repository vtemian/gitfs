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


from errno import ENOENT
from stat import S_IFDIR

from gitfs.fuse_compat import FuseOSError

from .read_only import ReadOnlyView


class IndexView(ReadOnlyView):
    def __init__(self, *args, **kwargs):
        super(ReadOnlyView, self).__init__(*args, **kwargs)

        self.current_path = kwargs.get("current_path", "current")
        self.history_path = kwargs.get("history_path", "history")

    def getattr(self, path, fh=None):
        """
        Returns a dictionary with keys identical to the stat C structure of
        stat(2).

        st_atime, st_mtime and st_ctime should be floats.

        NOTE: There is an incombatibility between Linux and Mac OS X
        concerning st_nlink of directories. Mac OS X counts all files inside
        the directory, while Linux counts only the subdirectories.
        """

        if path != "/":
            raise FuseOSError(ENOENT)

        attrs = super().getattr(path, fh)
        attrs.update({"st_mode": S_IFDIR | 0o555, "st_nlink": 2})

        return attrs

    def readdir(self, path, fh):
        yield from [".", "..", self.current_path, self.history_path]
