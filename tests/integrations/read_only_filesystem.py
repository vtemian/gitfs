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

import pytest

from tests.integrations.base import BaseTest


class ReadOnlyFSTest(BaseTest):
    path = ""

    def test_write_to_new_file(self):
        filename = f"{self.path}/new_file"
        content = "Read only filesystem"

        # FUSE3 may raise OSError instead of IOError, and message format may differ
        with pytest.raises((IOError, OSError)) as err:
            with open(filename, "w") as f:
                f.write(content)

        # FUSE3 behavior: For read-only filesystems, various errno values are acceptable:
        # - EROFS: Read-only file system (traditional)
        # - EPERM: Operation not permitted  
        # - EACCES: Permission denied
        # - ENOENT: No such file or directory (when trying to create in read-only path)
        assert err.value.errno in [errno.EROFS, errno.EPERM, errno.EACCES, errno.ENOENT]
        
        # For ENOENT, we should verify it's happening in a read-only context
        if err.value.errno == errno.ENOENT:
            # This is acceptable for FUSE3 read-only filesystems when trying to create files
            # The path should contain indicators that it's a read-only view (history, commit, etc.)
            assert any(readonly_indicator in self.path for readonly_indicator in ["history", "commit"]), \
                f"ENOENT error should only occur in read-only paths, but got path: {self.path}"
        else:
            # For other error codes, check the error message format
            error_str = str(err.value).lower()
            assert any(phrase in error_str for phrase in [
                "read-only file system", 
                "readonly file system",
                "operation not permitted",
                "permission denied"
            ])
