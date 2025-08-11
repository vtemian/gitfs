#!/usr/bin/env python3
"""
Comprehensive GitFS functionality test.
Tests mounting, reading, writing, and git operations.
"""

import os
import sys
import time
import subprocess
import tempfile
from pathlib import Path
import shutil

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

def run_test(test_name, test_func):
    """Run a single test and report results."""
    try:
        test_func()
        print(f"✓ {test_name}")
        return True
    except AssertionError as e:
        print(f"✗ {test_name}: {e}")
        return False
    except Exception as e:
        print(f"✗ {test_name}: Unexpected error - {e}")
        return False

def test_gitfs_full():
    """Comprehensive GitFS test."""
    
    # Create test directories
    test_dir = Path("/tmp/gitfs-full-test")
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
        shutil.rmtree(repo_dir)
    
    print(f"Mount point: {mount_point}")
    print(f"Repo dir: {repo_dir}")
    print(f"Log file: {log_file}")
    
    # Start GitFS
    cmd = [
        "python3", "-m", "gitfs.mounter",
        "https://github.com/octocat/Hello-World.git",
        str(mount_point),
        "-o",
        f"repo_path={repo_dir},branch=master,foreground=true,debug=true,log={log_file}"
    ]
    
    print(f"\nStarting GitFS...")
    
    # Start GitFS process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Give it time to mount
    time.sleep(3)
    
    # Check if process is still running
    if process.poll() is not None:
        print(f"ERROR: GitFS process died with code {process.returncode}")
        output, _ = process.communicate()
        print("Process output:")
        print(output)
        return False
    
    print("GitFS started successfully\n")
    print("Running tests:")
    print("-" * 40)
    
    all_passed = True
    
    # Test 1: Mount point check
    def test_mount():
        result = subprocess.run(
            ["mountpoint", str(mount_point)],
            capture_output=True
        )
        assert result.returncode == 0, "Mount point not active"
    
    all_passed &= run_test("Mount point is active", test_mount)
    
    # Test 2: Root directory structure
    def test_root_structure():
        entries = sorted(os.listdir(mount_point))
        assert entries == ["current", "history"], f"Expected ['current', 'history'], got {entries}"
    
    all_passed &= run_test("Root directory structure", test_root_structure)
    
    # Test 3: Current directory access
    def test_current_dir():
        current_dir = mount_point / "current"
        assert current_dir.exists(), "current directory doesn't exist"
        assert current_dir.is_dir(), "current is not a directory"
        
        # Should contain README file from Hello-World repo
        readme = current_dir / "README"
        assert readme.exists(), "README file not found in current"
    
    all_passed &= run_test("Current directory access", test_current_dir)
    
    # Test 4: Read file from current
    def test_read_file():
        readme = mount_point / "current" / "README"
        content = readme.read_text()
        assert "Hello World" in content, "README doesn't contain expected content"
    
    all_passed &= run_test("Read file from current", test_read_file)
    
    # Test 5: History directory access
    def test_history_dir():
        history_dir = mount_point / "history"
        assert history_dir.exists(), "history directory doesn't exist"
        assert history_dir.is_dir(), "history is not a directory"
        
        # Should have date directories
        entries = os.listdir(history_dir)
        assert len(entries) > 0, "history directory is empty"
    
    all_passed &= run_test("History directory access", test_history_dir)
    
    # Test 6: Write operation in current (should work)
    def test_write_current():
        test_file = mount_point / "current" / "test_file.txt"
        test_content = "This is a test file created by GitFS test\n"
        
        # Write file
        test_file.write_text(test_content)
        
        # Verify it was written
        assert test_file.exists(), "Test file wasn't created"
        assert test_file.read_text() == test_content, "File content doesn't match"
        
        # Clean up
        test_file.unlink()
    
    all_passed &= run_test("Write file in current", test_write_current)
    
    # Test 7: Write operation in history (should fail - read-only)
    def test_write_history():
        history_dir = mount_point / "history"
        test_file = history_dir / "test_file.txt"
        
        try:
            test_file.write_text("This should fail")
            assert False, "Write to history should have failed"
        except (PermissionError, OSError):
            pass  # Expected
    
    all_passed &= run_test("History is read-only", test_write_history)
    
    # Test 8: Directory operations
    def test_directory_ops():
        test_dir = mount_point / "current" / "test_directory"
        
        # Create directory
        test_dir.mkdir()
        assert test_dir.exists(), "Directory wasn't created"
        assert test_dir.is_dir(), "Created path is not a directory"
        
        # Create file in directory
        test_file = test_dir / "nested_file.txt"
        test_file.write_text("Nested file content")
        assert test_file.exists(), "Nested file wasn't created"
        
        # Clean up
        test_file.unlink()
        test_dir.rmdir()
    
    all_passed &= run_test("Directory operations", test_directory_ops)
    
    print("-" * 40)
    
    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")
    
    # Show last few log lines
    if log_file.exists():
        print(f"\nLast 10 lines of log:")
        with open(log_file) as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print(f"  {line.rstrip()}")
    
    # Clean up
    print("\nCleaning up...")
    cleanup(str(mount_point), process)
    
    return all_passed

if __name__ == "__main__":
    print("GitFS Comprehensive Test")
    print("=" * 50)
    
    success = test_gitfs_full()
    
    if not success:
        sys.exit(1)