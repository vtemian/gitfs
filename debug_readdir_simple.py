#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, '/vagrant')

def test_readdir_direct():
    """Test readdir operation directly without router caching"""
    
    from gitfs.views.index import IndexView
    from gitfs.repository import Repository
    from pygit2 import RemoteCallbacks
    
    # Create a test repository (minimal setup)
    repo_path = "/tmp/test_repo_debug" 
    if os.path.exists(repo_path):
        import shutil
        shutil.rmtree(repo_path)
    
    # Clone repo directly
    credentials = RemoteCallbacks()
    repo = Repository.clone("/tmp/gitfs-tests/testing_repo.git", repo_path, "main", credentials)
    
    # Create IndexView directly
    view = IndexView(
        repo=repo,
        mount_path="/tmp/test_mount",
        current_path="current", 
        history_path="history",
        uid=1000,
        gid=1000,
        mount_time=1234567890,
    )
    
    print("=== Testing IndexView directly ===")
    
    # Test getattr for root
    try:
        attrs = view.getattr("/")
        print(f"✓ getattr('/'): mode={oct(attrs.get('st_mode', 0))}, nlink={attrs.get('st_nlink', 0)}")
    except Exception as e:
        print(f"✗ getattr('/') failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test readdir for root
    try:
        entries = view.readdir("/", None)
        print(f"✓ readdir('/'): {entries}")
        print(f"  Entry count: {len(entries)}")
        for i, entry in enumerate(entries):
            print(f"  [{i}]: '{entry}' (type: {type(entry)})")
    except Exception as e:
        print(f"✗ readdir('/') failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with empty path
    try:
        entries = view.readdir("", None)  
        print(f"✓ readdir(''): {entries}")
    except Exception as e:
        print(f"✗ readdir('') failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Clean up
    try:
        import shutil
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
    except:
        pass

if __name__ == '__main__':
    test_readdir_direct()