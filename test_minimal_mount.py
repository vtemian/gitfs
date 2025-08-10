#!/usr/bin/env python3

import sys
import os
import tempfile
import time

sys.path.insert(0, '/vagrant')

from gitfs.fuse_compat import FUSE, Operations, FuseOSError
from errno import ENOENT
from stat import S_IFDIR, S_IFREG


class SimpleFS(Operations):
    """Minimal test filesystem to verify FUSE3 mounting works"""
    
    def __init__(self):
        self.files = {
            '/': dict(st_mode=(S_IFDIR | 0o755), st_ctime=time.time(), st_mtime=time.time(), st_atime=time.time()),
            '/hello': dict(st_mode=(S_IFREG | 0o644), st_ctime=time.time(), st_mtime=time.time(), st_atime=time.time(), st_size=13),
        }
        
    def getattr(self, path, fh=None):
        if path not in self.files:
            raise FuseOSError(ENOENT)
        return self.files[path]
    
    def readdir(self, path, fh):
        if path == '/':
            return ['.', '..', 'hello']
        else:
            raise FuseOSError(ENOENT)
    
    def read(self, path, length, offset, fh):
        if path == '/hello':
            data = b'Hello World!\n'
            return data[offset:offset + length]
        else:
            raise FuseOSError(ENOENT)

def main():
    mount_point = '/tmp/test_simple_mount'
    
    # Clean up if exists
    os.system(f'umount {mount_point} 2>/dev/null || true')
    os.makedirs(mount_point, exist_ok=True)
    
    print(f"Testing simple FUSE3 mount at {mount_point}")
    
    try:
        # Try basic mounting with minimal options
        FUSE(SimpleFS(), mount_point, foreground=True, allow_other=False)
    except Exception as e:
        print(f"Mount failed: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())