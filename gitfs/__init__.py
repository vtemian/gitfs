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

__version__ = "0.5.2"


def mount():
    # Setup FUSE3 before any imports that use mfusepy
    import os
    import platform

    # Set FUSE library path before importing mfusepy for FUSE3 support
    if not os.environ.get("FUSE_LIBRARY_PATH"):
        # Detect system architecture
        machine = platform.machine()

        # Common FUSE3 library paths
        fuse3_paths = [
            f"/usr/lib/{machine}-linux-gnu/libfuse3.so.3",
            "/usr/lib/x86_64-linux-gnu/libfuse3.so.3",
            "/usr/lib/aarch64-linux-gnu/libfuse3.so.3",
            "/usr/lib64/libfuse3.so.3",
            "/usr/local/lib/libfuse3.so.3",
        ]

        # Check for FUSE3 library
        for path in fuse3_paths:
            if os.path.exists(path):
                os.environ["FUSE_LIBRARY_PATH"] = path
                break

    # Now import start_fuse after FUSE3 is configured
    from gitfs.mounter import start_fuse

    start_fuse()
