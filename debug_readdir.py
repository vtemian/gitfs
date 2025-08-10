#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, '/vagrant')

def test_readdir_routing():
    """Test readdir operation routing and implementation"""
    
    # Fix cache size issue
    from gitfs.cache import lru_cache
    lru_cache.maxsize = 800  # Set reasonable cache size
    
    from gitfs.router import Router
    from gitfs.routes import prepare_routes
    from gitfs.utils import Args
    from gitfs.worker import CommitQueue
    from pygit2 import RemoteCallbacks
    
    # Mock args
    class MockArgs:
        current_path = 'current'
        history_path = 'history'
        foreground = True
        allow_other = False
        allow_root = False
    
    args = MockArgs()
    
    # Set up router
    commit_queue = CommitQueue()
    credentials = RemoteCallbacks()
    
    router = Router(
        remote_url="/tmp/gitfs-tests/testing_repo.git",
        mount_path="/tmp/test_mount",
        current_path="current",
        history_path="history",
        repo_path="/tmp/test_repo_debug",
        branch="main",
        user="vagrant",
        group="vagrant",
        max_size=10 * 1024 * 1024,
        max_offset=10 * 1024 * 1024,
        commit_queue=commit_queue,
        credentials=credentials,
        ignore_file=None,
        hard_ignore=None,
    )
    
    # register routes
    routes = prepare_routes(args)
    router.register(routes)
    
    # Test routing for root path
    paths_to_test = ["/", ""]
    
    for path in paths_to_test:
        print(f"\n=== Testing path '{path}' ===")
        
        try:
            view, relative_path = router.get_view(path)
            print(f"✓ Routing successful:")
            print(f"  View: {view.__class__.__name__}")
            print(f"  Relative path: '{relative_path}'")
            
            # Test getattr
            try:
                attrs = view.getattr(relative_path)
                print(f"✓ getattr successful: mode={oct(attrs.get('st_mode', 0))}")
            except Exception as e:
                print(f"✗ getattr failed: {e}")
                
            # Test readdir
            try:
                entries = view.readdir(relative_path, None)
                print(f"✓ readdir successful: {entries}")
            except Exception as e:
                print(f"✗ readdir failed: {e}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"✗ Routing failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Clean up
    try:
        import shutil
        if os.path.exists("/tmp/test_repo_debug"):
            shutil.rmtree("/tmp/test_repo_debug")
    except:
        pass

if __name__ == '__main__':
    test_readdir_routing()