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


"""
FUSE compatibility layer for cross-platform support.

This module provides a unified interface for FUSE operations across different
platforms and FUSE versions (FUSE2 vs FUSE3).
"""

import platform
import sys
from ctypes.util import find_library

# Global variables to track which FUSE implementation is being used
_fuse_module = None
_is_fuse3 = False


def _detect_fuse_version():
    """Detect available FUSE version and return appropriate module."""
    global _fuse_module, _is_fuse3

    if _fuse_module is not None:
        return _fuse_module

    system = platform.system()

    # Try to import available FUSE libraries in order of preference
    fuse_libraries = []

    if system == "Darwin":
        # On macOS, prefer fusepy (FUSE2) as it's more compatible with MacFUSE
        # Note: fusepy package installs as 'fuse' module, not 'fusepy'
        fuse_libraries = [
            ("fuse", False),  # fusepy installs as 'fuse' module (FUSE2)
            ("mfusepy", False),  # Try mfusepy as FUSE2 fallback
        ]
    else:
        # On Linux, prefer FUSE3 (mfusepy) if available
        fuse3_lib = find_library("fuse3")
        if fuse3_lib:
            fuse_libraries.append(("mfusepy", True))

        # Always add FUSE2 as fallback (fusepy installs as 'fuse')
        fuse_libraries.append(("fuse", False))

    # Try each library in order
    last_error = None
    for module_name, is_fuse3_flag in fuse_libraries:
        try:
            module = __import__(module_name)

            # Test that the module has essential FUSE classes
            if not (hasattr(module, "FUSE") and hasattr(module, "FuseOSError")):
                continue

            _fuse_module = module
            _is_fuse3 = is_fuse3_flag

            # For mfusepy on macOS, ensure it uses FUSE2 library
            if system == "Darwin" and module_name == "mfusepy" and not is_fuse3_flag:
                fuse2_lib = find_library("fuse")
                if fuse2_lib and hasattr(module, "_libfuse_path"):
                    # Set the library path before it gets loaded
                    module._libfuse_path = fuse2_lib

            return module
        except (ImportError, OSError) as e:
            # Store the last error for reporting
            last_error = e
            continue

    error_msg = (
        "No compatible FUSE library found. Please install fusepy or mfusepy.\n"
        f"Platform: {system}, Available libraries: {[name for name, _ in fuse_libraries]}"
    )
    if last_error:
        error_msg += f"\nLast error: {last_error}"

    raise ImportError(error_msg)


def get_fuse_module():
    """Get the appropriate FUSE module for this platform."""
    return _detect_fuse_version()


def is_fuse3():
    """Return True if using FUSE3, False if using FUSE2."""
    _detect_fuse_version()  # Ensure detection has run
    return _is_fuse3


def get_fuse_version():
    """Get FUSE version information."""
    module = get_fuse_module()

    if hasattr(module, "fuse_version_major"):
        return f"{module.fuse_version_major}.{module.fuse_version_minor}"
    elif hasattr(module, "FUSE_VERSION"):
        return str(module.FUSE_VERSION)
    else:
        return "unknown"


# Export the key classes and exceptions from the detected module
def __getattr__(name):
    """Dynamically export FUSE classes and functions from the detected module."""
    module = get_fuse_module()

    if hasattr(module, name):
        return getattr(module, name)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
