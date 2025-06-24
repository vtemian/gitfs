# Copyright 2014-2016 Presslabs SRL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for Git LFS functionality."""

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from gitfs.lfs import LFSManager, LFSPointer


class TestLFSPointer(unittest.TestCase):
    """Test LFS pointer file handling."""

    def test_create_pointer(self):
        """Test creating an LFS pointer."""
        pointer = LFSPointer("abc123", 12345)
        self.assertEqual(pointer.oid, "abc123")
        self.assertEqual(pointer.size, 12345)
        self.assertEqual(pointer.version, LFSPointer.VERSION_V1)

    def test_pointer_to_content(self):
        """Test converting pointer to file content."""
        pointer = LFSPointer("abcdef123456", 98765)
        content = pointer.to_content()
        expected = (
            "version https://git-lfs.github.com/spec/v1\n"
            "oid sha256:abcdef123456\n"
            "size 98765\n"
        )
        self.assertEqual(content.decode("utf-8"), expected)

    def test_pointer_from_content_valid(self):
        """Test parsing valid pointer content."""
        content = (
            "version https://git-lfs.github.com/spec/v1\n"
            "oid sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef\n"
            "size 123456\n"
        ).encode("utf-8")
        
        pointer = LFSPointer.from_content(content)
        self.assertIsNotNone(pointer)
        self.assertEqual(pointer.oid, "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
        self.assertEqual(pointer.size, 123456)

    def test_pointer_from_content_invalid(self):
        """Test parsing invalid content returns None."""
        invalid_contents = [
            b"This is not a pointer file",
            b"version wrong\noid sha256:abc\nsize 123\n",
            b"version https://git-lfs.github.com/spec/v1\noid invalid\nsize abc\n",
            b"incomplete content",
            b"",  # empty content
        ]
        
        for content in invalid_contents:
            with self.subTest(content=content):
                pointer = LFSPointer.from_content(content)
                self.assertIsNone(pointer)

    def test_pointer_legacy_version(self):
        """Test parsing legacy version pointer."""
        content = (
            "version https://hawser.github.com/spec/v1\n"
            "oid sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef\n"
            "size 123456\n"
        ).encode("utf-8")
        
        pointer = LFSPointer.from_content(content)
        self.assertIsNotNone(pointer)
        self.assertEqual(pointer.version, LFSPointer.VERSION_LEGACY)

    def test_is_pointer(self):
        """Test pointer detection."""
        valid_content = (
            "version https://git-lfs.github.com/spec/v1\n"
            "oid sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef\n"
            "size 123456\n"
        ).encode("utf-8")
        
        invalid_content = b"This is regular file content"
        
        self.assertTrue(LFSPointer.is_pointer(valid_content))
        self.assertFalse(LFSPointer.is_pointer(invalid_content))

    def test_create_for_file(self):
        """Test creating pointer for an actual file."""
        content = b"This is test file content for LFS"
        expected_hash = hashlib.sha256(content).hexdigest()
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            f.flush()
            
            pointer = LFSPointer.create_for_file(f.name)
            
            self.assertEqual(pointer.oid, expected_hash)
            self.assertEqual(pointer.size, len(content))
            
            # Clean up
            Path(f.name).unlink()


class TestLFSManager(unittest.TestCase):
    """Test LFS manager functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_dir = self.temp_dir / "repo"
        self.repo_dir.mkdir()
        (self.repo_dir / ".git").mkdir()
        
        self.lfs_manager = LFSManager(
            str(self.repo_dir),
            enabled=True,
            size_threshold=1.0,  # 1MB
            auto_fetch=True,
            auto_push=True
        )

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_init_with_config(self):
        """Test LFS manager initialization with configuration."""
        manager = LFSManager(
            str(self.repo_dir),
            enabled=False,
            size_threshold=50.0,
            auto_fetch=False,
            auto_push=False
        )
        
        self.assertFalse(manager.enabled)
        self.assertEqual(manager.size_threshold, 50 * 1024 * 1024)  # 50MB in bytes
        self.assertFalse(manager.auto_fetch)
        self.assertFalse(manager.auto_push)

    def test_is_lfs_enabled_disabled(self):
        """Test LFS enabled check when disabled in config."""
        manager = LFSManager(str(self.repo_dir), enabled=False)
        self.assertFalse(manager.is_lfs_enabled())

    @patch('subprocess.run')
    def test_is_lfs_enabled_git_check(self, mock_run):
        """Test LFS enabled check with git command."""
        # Mock successful git lfs env command
        mock_run.return_value = Mock(returncode=0)
        self.assertTrue(self.lfs_manager.is_lfs_enabled())
        
        # Mock failed git lfs env command
        mock_run.return_value = Mock(returncode=1)
        self.assertFalse(self.lfs_manager.is_lfs_enabled())

    def test_get_lfs_object_path(self):
        """Test LFS object path generation."""
        oid = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        expected_path = self.repo_dir / ".git" / "lfs" / "objects" / "ab" / "cd" / oid
        
        actual_path = self.lfs_manager.get_lfs_object_path(oid)
        self.assertEqual(actual_path, expected_path)

    def test_should_use_lfs_disabled(self):
        """Test should_use_lfs when LFS is disabled."""
        manager = LFSManager(str(self.repo_dir), enabled=False)
        self.assertFalse(manager.should_use_lfs("test.txt", 1000))

    def test_should_use_lfs_size_threshold(self):
        """Test should_use_lfs based on size threshold."""
        # File larger than threshold should use LFS
        large_size = 2 * 1024 * 1024  # 2MB (threshold is 1MB)
        self.assertTrue(self.lfs_manager.should_use_lfs("large.txt", large_size))
        
        # File smaller than threshold should not use LFS (unless in gitattributes)
        small_size = 500 * 1024  # 500KB
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(stdout="", returncode=0)
            self.assertFalse(self.lfs_manager.should_use_lfs("small.txt", small_size))

    @patch('subprocess.run')
    def test_should_use_lfs_gitattributes(self, mock_run):
        """Test should_use_lfs based on gitattributes."""
        # Mock git check-attr returning lfs filter
        mock_run.return_value = Mock(stdout="test.bin: filter: lfs", returncode=0)
        
        small_size = 100  # Very small file
        self.assertTrue(self.lfs_manager.should_use_lfs("test.bin", small_size))

    def test_store_and_retrieve_lfs_object(self):
        """Test storing and retrieving LFS objects."""
        content = b"Test LFS object content"
        oid = hashlib.sha256(content).hexdigest()
        
        # Store object
        self.lfs_manager.store_lfs_object(content, oid)
        
        # Check object exists
        self.assertTrue(self.lfs_manager.has_lfs_object(oid))
        
        # Create pointer and retrieve content
        pointer = LFSPointer(oid, len(content))
        retrieved_content = self.lfs_manager.get_lfs_object_content(pointer)
        
        self.assertEqual(retrieved_content, content)

    def test_get_lfs_object_content_missing(self):
        """Test retrieving content for missing LFS object."""
        pointer = LFSPointer("nonexistent", 123)
        content = self.lfs_manager.get_lfs_object_content(pointer)
        self.assertIsNone(content)

    @patch('subprocess.run')
    def test_fetch_lfs_objects(self, mock_run):
        """Test LFS objects fetch."""
        mock_run.return_value = Mock(returncode=0)
        self.assertTrue(self.lfs_manager.fetch_lfs_objects())
        
        mock_run.assert_called_with(
            ["git", "lfs", "fetch"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
        )

    @patch('subprocess.run')
    def test_push_lfs_objects(self, mock_run):
        """Test LFS objects push."""
        mock_run.return_value = Mock(returncode=0)
        self.assertTrue(self.lfs_manager.push_lfs_objects())
        
        mock_run.assert_called_with(
            ["git", "lfs", "push", "--all", "origin"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
        )


if __name__ == "__main__":
    unittest.main()