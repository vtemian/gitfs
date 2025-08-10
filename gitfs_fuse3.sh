#!/bin/bash

# GitFS wrapper script to force FUSE 3 usage

echo "=== GitFS FUSE 3 Wrapper ==="

# Force FUSE 3 library path
if [ -z "$FUSE_LIBRARY_PATH" ]; then
    # Try common FUSE 3 library locations
    FUSE3_PATHS=(
        "/usr/lib/$(uname -m)-linux-gnu/libfuse3.so.3"
        "/usr/lib/x86_64-linux-gnu/libfuse3.so.3"
        "/usr/lib/aarch64-linux-gnu/libfuse3.so.3"
        "/usr/lib64/libfuse3.so.3"
        "/usr/local/lib/libfuse3.so.3"
    )
    
    for path in "${FUSE3_PATHS[@]}"; do
        if [ -f "$path" ]; then
            export FUSE_LIBRARY_PATH="$path"
            echo "Using FUSE 3 library: $path"
            break
        fi
    done
    
    if [ -z "$FUSE_LIBRARY_PATH" ]; then
        echo "Warning: FUSE 3 library not found, using default"
    fi
else
    echo "FUSE_LIBRARY_PATH already set: $FUSE_LIBRARY_PATH"
fi

# Test the library
echo "Testing library loading..."
python3 test_fuse_library.py

echo
echo "Starting GitFS with FUSE 3..."

# Run GitFS with the forced library
exec gitfs "$@"