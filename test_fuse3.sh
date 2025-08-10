#!/bin/bash

echo "=== Testing GitFS with FUSE 3 ==="
echo

# Set FUSE 3 library path for your system
export FUSE_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/libfuse3.so.3

echo "FUSE_LIBRARY_PATH set to: $FUSE_LIBRARY_PATH"
echo

# Test Python environment
echo "=== Testing FUSE 3 configuration ==="
python3 check_fuse3_mfusepy.py
echo

echo "=== Ready to test GitFS ==="
echo "You can now run GitFS with FUSE 3 support:"
echo "  gitfs <remote_url> <mount_point>"
echo
echo "Or test with:"
echo "  python -m gitfs <remote_url> <mount_point>"