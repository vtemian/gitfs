#!/usr/bin/env python3

import os
import sys
import tempfile
import subprocess
import time

def test_basic_operations():
    """Test basic FUSE operations to identify what's failing"""
    
    # Test mount point
    mount_point = "/tmp/test_mount"
    
    print("=== Debugging FUSE Operations ===")
    print(f"Mount point: {mount_point}")
    
    # Check if mounted
    result = subprocess.run(["mount"], capture_output=True, text=True)
    if mount_point in result.stdout:
        print("✓ Mount point is mounted")
    else:
        print("✗ Mount point is not mounted")
        return
    
    # Test 1: Basic stat (getattr)
    print("\n1. Testing stat (getattr):")
    try:
        stat = os.stat(mount_point)
        print(f"✓ stat succeeded: mode={oct(stat.st_mode)}, size={stat.st_size}")
    except Exception as e:
        print(f"✗ stat failed: {e}")
    
    # Test 2: Access permissions
    print("\n2. Testing access:")
    try:
        can_read = os.access(mount_point, os.R_OK)
        can_write = os.access(mount_point, os.W_OK)
        can_exec = os.access(mount_point, os.X_OK)
        print(f"✓ access: read={can_read}, write={can_write}, exec={can_exec}")
    except Exception as e:
        print(f"✗ access failed: {e}")
    
    # Test 3: opendir
    print("\n3. Testing opendir:")
    try:
        fd = os.open(mount_point, os.O_RDONLY)
        print(f"✓ opendir succeeded: fd={fd}")
        os.close(fd)
    except Exception as e:
        print(f"✗ opendir failed: {e}")
    
    # Test 4: readdir using os.listdir
    print("\n4. Testing readdir (os.listdir):")
    try:
        entries = os.listdir(mount_point)
        print(f"✓ readdir succeeded: entries={entries}")
    except Exception as e:
        print(f"✗ readdir failed: {e}")
    
    # Test 5: readdir using os.scandir
    print("\n5. Testing readdir (os.scandir):")
    try:
        with os.scandir(mount_point) as entries:
            entry_names = [entry.name for entry in entries]
        print(f"✓ scandir succeeded: entries={entry_names}")
    except Exception as e:
        print(f"✗ scandir failed: {e}")
    
    # Test 6: Raw system call tracing
    print("\n6. Testing with strace:")
    result = subprocess.run(
        ["strace", "-e", "trace=openat,getdents64,getdents", "ls", mount_point],
        capture_output=True,
        text=True
    )
    print(f"strace return code: {result.returncode}")
    if result.stderr:
        # Look for specific syscalls
        lines = result.stderr.split('\n')
        for line in lines:
            if 'openat' in line or 'getdents' in line:
                print(f"  {line}")
    
    print(f"strace stdout: {result.stdout}")

if __name__ == "__main__":
    test_basic_operations()