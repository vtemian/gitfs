#!/bin/bash

# Script to install FUSE 3 on Ubuntu/Debian systems

echo "=== Installing FUSE 3 ==="
echo "This script will help you upgrade from FUSE 2 to FUSE 3"
echo

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run this script with sudo:"
    echo "sudo bash install_fuse3.sh"
    exit 1
fi

# Update package list
echo "Updating package list..."
apt-get update

# Install FUSE 3
echo "Installing FUSE 3 packages..."
apt-get install -y fuse3 libfuse3-dev libfuse3-3

# Check installation
echo
echo "=== Checking FUSE 3 Installation ==="
if command -v fusermount3 &> /dev/null; then
    echo "✓ fusermount3 installed:"
    fusermount3 --version
else
    echo "✗ fusermount3 not found"
fi

if pkg-config --exists fuse3; then
    echo "✓ FUSE 3 development files installed:"
    pkg-config --modversion fuse3
else
    echo "✗ FUSE 3 development files not found"
fi

# Check for libfuse3
echo
echo "=== Checking libfuse3 ==="
ldconfig -p | grep libfuse3

echo
echo "=== Installation complete! ==="
echo "FUSE 3 has been installed. You may need to:"
echo "1. Restart your Vagrant box"
echo "2. Update your Python bindings to use a FUSE 3 compatible library"
echo
echo "Note: FUSE 2 and FUSE 3 can coexist on the same system."