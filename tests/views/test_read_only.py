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


import os

import pytest
from gitfs.fuse_compat import FuseOSError

from gitfs.views.read_only import ReadOnlyView


class TestReadOnly:
    def test_cant_write(self):
        view = ReadOnlyView()

        # Test methods with their proper signatures
        with pytest.raises(FuseOSError):
            view.write("path", b"data", 0, 1)  # write(path, buf, offset, fh)
            
        with pytest.raises(FuseOSError):
            view.create("path", 0o644)  # create(path, mode, fi=None)
            
        with pytest.raises(FuseOSError):
            view.utimens("path")  # utimens(path, times=None)
            
        with pytest.raises(FuseOSError):
            view.chmod("path", 0o644)  # chmod(path, mode)
            
        with pytest.raises(FuseOSError):
            view.mkdir("path", 0o755)  # mkdir(path, mode)

        with pytest.raises(FuseOSError):
            view.getxattr("path", "name", 1)

        with pytest.raises(FuseOSError):
            view.chown("path", 1, 1)

    def test_always_return_0(self):
        view = ReadOnlyView()

        for method in ["flush", "releasedir", "release"]:
            assert getattr(view, method)("path", 1) == 0

        assert view.opendir("path") == 0

    def test_open(self):
        view = ReadOnlyView()

        with pytest.raises(FuseOSError):
            view.open("path", os.O_WRONLY)
        assert view.open("path", os.O_RDONLY) == 0

    def test_access(self):
        view = ReadOnlyView()

        with pytest.raises(FuseOSError):
            view.access("path", os.W_OK)
        assert view.access("path", os.R_OK) == 0
