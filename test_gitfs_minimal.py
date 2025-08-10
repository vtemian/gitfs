#!/usr/bin/env python3

import sys
import os
import time

sys.path.insert(0, '/vagrant')

def test_gitfs_minimal():
    """Test GitFS with minimal mount options"""
    
    # Set FUSE2 library path for testing
    # os.environ["FUSE_LIBRARY_PATH"] = "/usr/lib/aarch64-linux-gnu/libfuse3.so.3"
    
    from gitfs.router import Router
    from gitfs.routes import prepare_routes
    from gitfs.utils import Args
    from gitfs.fuse_compat import FUSE, is_fuse3, get_fuse_version
    from gitfs.worker import CommitQueue
    from pygit2 import RemoteCallbacks
    
    print(f"FUSE version: {get_fuse_version()}, is_fuse3: {is_fuse3()}")
    
    # Mock args
    class MockArgs:
        current_path = 'current'
        history_path = 'history'
        foreground = True
        allow_other = False
        allow_root = False
    
    args = MockArgs()
    
    # Set up minimal router configuration
    commit_queue = CommitQueue()
    credentials = RemoteCallbacks()
    
    router = Router(
        remote_url="/tmp/gitfs-tests/testing_repo.git",
        mount_path="/tmp/test_mount",
        current_path="current",
        history_path="history",
        repo_path="/tmp/test_repo",
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
    
    mount_point = "/tmp/test_mount"
    
    # Clean up
    os.system(f'umount {mount_point} 2>/dev/null || true')
    os.makedirs(mount_point, exist_ok=True)
    
    print(f"Attempting to mount GitFS at {mount_point}")
    
    # Debug: Check if FUSE3 operations are available
    print(f"Router has copy_file_range: {hasattr(router, 'copy_file_range')}")
    print(f"Router has lseek: {hasattr(router, 'lseek')}")
    
    # Use absolutely minimal mount options
    fuse_kwargs = {
        "foreground": True,
    }
    
    try:
        # Use FUSE3Wrapper for mfusepy compatibility
        if is_fuse3():
            # Create a wrapper that adds FUSE3 operations to the FUSE object
            class FUSE3Wrapper(FUSE):
                def __init__(self, operations, *args, **kwargs):
                    # Add FUSE3 operations to the FUSE object itself
                    for op_name in ["copy_file_range", "lseek", "init_with_config"]:
                        if hasattr(operations, op_name):
                            # Bind the operation from the operations object to this FUSE object
                            setattr(self, op_name, getattr(operations, op_name))
                        else:
                            # Provide a default implementation if missing
                            def default_op(*args, **kwargs):
                                from errno import ENOSYS
                                from gitfs.fuse_compat import FuseOSError
                                raise FuseOSError(ENOSYS)
                            setattr(self, op_name, default_op)

                    super().__init__(operations, *args, **kwargs)

            FUSE3Wrapper(router, mount_point, **fuse_kwargs)
        else:
            FUSE(router, mount_point, **fuse_kwargs)
            
        print("Mount succeeded!")
    except Exception as e:
        print(f"Mount failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(test_gitfs_minimal())