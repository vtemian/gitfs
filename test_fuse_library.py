#!/usr/bin/env python3
"""
Test script to verify FUSE 3 library loading
"""

import os
import platform
import ctypes.util

def test_fuse_library():
    print("=== FUSE Library Detection Test ===")
    
    # Check current environment
    print(f"Current FUSE_LIBRARY_PATH: {os.environ.get('FUSE_LIBRARY_PATH', 'Not set')}")
    
    # Check system architecture
    machine = platform.machine()
    print(f"System architecture: {machine}")
    
    # Try to find FUSE 3 library
    print("\n=== Library Detection ===")
    
    # FUSE 3
    fuse3_lib = ctypes.util.find_library('fuse3')
    print(f"FUSE 3 library: {fuse3_lib}")
    
    # Check common FUSE 3 paths
    print("\n=== FUSE 3 Path Check ===")
    fuse3_paths = [
        f'/usr/lib/{machine}-linux-gnu/libfuse3.so.3',
        '/usr/lib/x86_64-linux-gnu/libfuse3.so.3',
        '/usr/lib/aarch64-linux-gnu/libfuse3.so.3',
        '/usr/lib64/libfuse3.so.3',
        '/usr/local/lib/libfuse3.so.3',
    ]
    
    for path in fuse3_paths:
        exists = os.path.exists(path)
        print(f"  {path}: {'✓' if exists else '✗'}")
        if exists:
            fuse3_found = path
            break
    else:
        fuse3_found = None
    
    # Force FUSE 3 and test
    print("\n=== Testing FUSE 3 Force ===")
    if fuse3_found:
        os.environ['FUSE_LIBRARY_PATH'] = fuse3_found
        print(f"Set FUSE_LIBRARY_PATH to: {fuse3_found}")
    elif fuse3_lib:
        os.environ['FUSE_LIBRARY_PATH'] = fuse3_lib
        print(f"Set FUSE_LIBRARY_PATH to: {fuse3_lib}")
    else:
        print("No FUSE 3 library found!")
        return
    
    # Now test mfusepy import
    print("\n=== Testing mfusepy Import ===")
    try:
        import mfusepy
        print(f"mfusepy imported successfully")
        print(f"FUSE version: {mfusepy.fuse_version_major}.{mfusepy.fuse_version_minor}")
        print(f"Library path: {getattr(mfusepy, '_libfuse_path', 'Unknown')}")
        print(f"Using FUSE 3: {mfusepy.fuse_version_major == 3}")
        
        if mfusepy.fuse_version_major == 3:
            print("✓ SUCCESS: mfusepy is using FUSE 3!")
        else:
            print(f"✗ WARNING: mfusepy is using FUSE {mfusepy.fuse_version_major}.{mfusepy.fuse_version_minor}")
            
    except Exception as e:
        print(f"Failed to import mfusepy: {e}")

if __name__ == "__main__":
    test_fuse_library()