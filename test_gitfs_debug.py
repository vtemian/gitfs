#!/usr/bin/env python3
"""
Debug script to test GitFS mounting and operation handling.
This helps identify why the transport endpoint gets disconnected.
"""

import os
import sys
import time
import subprocess
import tempfile
import signal
from pathlib import Path

def cleanup(mount_point, process=None):
    """Clean up mount point and process."""
    if process:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            try:
                process.kill()
            except:
                pass
    
    # Force unmount
    subprocess.run(["sudo", "umount", "-l", mount_point], 
                   stderr=subprocess.DEVNULL, check=False)
    time.sleep(0.5)

def test_gitfs():
    """Test GitFS mounting with detailed logging."""
    
    # Create test directories
    test_dir = Path("/tmp/gitfs-debug-test")
    test_dir.mkdir(exist_ok=True)
    
    mount_point = test_dir / "mount"
    repo_dir = test_dir / "repo"
    log_file = test_dir / "gitfs.log"
    
    # Clean up any existing mount
    cleanup(str(mount_point))
    
    # Ensure mount point exists
    mount_point.mkdir(exist_ok=True)
    
    # Remove old repo if exists
    if repo_dir.exists():
        import shutil
        shutil.rmtree(repo_dir)
    
    print(f"Mount point: {mount_point}")
    print(f"Repo dir: {repo_dir}")
    print(f"Log file: {log_file}")
    
    # Start GitFS with maximum debugging
    # Note: Hello-World repo uses 'master' branch, not 'main'
    cmd = [
        "python3", "-m", "gitfs.mounter",
        "https://github.com/octocat/Hello-World.git",
        str(mount_point),
        "-o",
        f"repo_path={repo_dir},branch=master,foreground=true,debug=true,log={log_file}"
    ]
    
    print(f"\nStarting GitFS with command:")
    print(" ".join(cmd))
    
    # Start GitFS process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Give it time to mount
    print("\nWaiting for mount...")
    time.sleep(3)
    
    # Check if process is still running
    if process.poll() is not None:
        print(f"ERROR: GitFS process died with code {process.returncode}")
        output, _ = process.communicate()
        print("Process output:")
        print(output)
        return False
    
    print("GitFS process is running")
    
    # Test filesystem operations
    print("\nTesting filesystem operations:")
    
    try:
        # Test 1: Check mount
        result = subprocess.run(
            ["mountpoint", str(mount_point)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Mount point is active")
        else:
            print(f"✗ Mount point check failed: {result.stderr}")
            
        # Test 2: List root directory
        print("\nAttempting to list root directory...")
        result = subprocess.run(
            ["ls", "-la", str(mount_point)],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ Directory listing successful:")
            print(result.stdout)
        else:
            print(f"✗ Directory listing failed: {result.stderr}")
            
        # Test 3: Check for expected directories
        current_dir = mount_point / "current"
        history_dir = mount_point / "history"
        
        if current_dir.exists():
            print("✓ 'current' directory exists")
        else:
            print("✗ 'current' directory not found")
            
        if history_dir.exists():
            print("✓ 'history' directory exists")
        else:
            print("✗ 'history' directory not found")
            
    except subprocess.TimeoutExpired:
        print("✗ Operation timed out - filesystem may be hung")
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
    
    # Check log file for errors
    if log_file.exists():
        print(f"\nLast 20 lines of log file:")
        with open(log_file) as f:
            lines = f.readlines()
            for line in lines[-20:]:
                print(line.rstrip())
    
    # Clean up
    print("\nCleaning up...")
    cleanup(str(mount_point), process)
    
    return True

if __name__ == "__main__":
    print("GitFS Debug Test")
    print("=" * 50)
    
    success = test_gitfs()
    
    if success:
        print("\nTest completed")
    else:
        print("\nTest failed")
        sys.exit(1)