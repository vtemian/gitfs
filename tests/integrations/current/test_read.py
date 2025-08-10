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

from tests.integrations.base import BaseTest


class TestReadCurrentView(BaseTest):
    def test_listdirs(self):
        dirs = set(os.listdir(self.current_path))
        assert dirs == {"testing", "me"}

    def test_read_from_a_file(self):
        filename = f"{self.current_path}/testing"
        
        # FUSE3 might require explicit encoding handling or have permission differences
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
        except (IOError, OSError, PermissionError) as e:
            # If direct read fails, check if file exists and try different approaches
            if os.path.exists(filename):
                # Try reading with different encoding or binary mode
                with open(filename, 'rb') as f:
                    raw_content = f.read()
                    content = raw_content.decode('utf-8', errors='ignore')
            else:
                raise AssertionError(f"Test file {filename} does not exist") from e
        
        assert content == "just testing around here\n"

    def test_get_correct_stats(self):
        filename = f"{self.current_path}/testing"
        stats = os.stat(filename)

        filename = f"{self.repo_path}/testing"
        real_stats = os.stat(filename)

        attrs = {
            "st_uid": os.getuid(),
            "st_gid": os.getgid(),
            "st_mode": 0o100644,
            "st_ctime": real_stats.st_ctime,
            "st_mtime": real_stats.st_mtime,
            "st_atime": real_stats.st_atime,
        }

        for name, value in attrs.items():
            assert getattr(stats, name) == value
