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

"""Git LFS (Large File Storage) support for GitFS."""

import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


class LFSPointer:
    """Represents a Git LFS pointer file."""

    VERSION_V1 = "https://git-lfs.github.com/spec/v1"
    VERSION_LEGACY = "https://hawser.github.com/spec/v1"
    MAX_POINTER_SIZE = 1024
    POINTER_PATTERN = re.compile(
        r"^version\s+(https://(?:git-lfs\.github\.com|hawser\.github\.com)/spec/v1)\n"
        r"oid\s+sha256:([a-f0-9]{64})\n"
        r"size\s+(\d+)\n?$",
        re.MULTILINE,
    )

    def __init__(self, oid: str, size: int, version: str = VERSION_V1):
        """Initialize LFS pointer.

        Args:
            oid: SHA256 hash of the file content
            size: Size of the file in bytes
            version: LFS spec version URL
        """
        self.oid = oid
        self.size = size
        self.version = version

    @classmethod
    def from_content(cls, content: bytes) -> Optional["LFSPointer"]:
        """Parse LFS pointer from file content.

        Args:
            content: Raw file content

        Returns:
            LFSPointer if content is a valid pointer, None otherwise
        """
        if len(content) > cls.MAX_POINTER_SIZE:
            return None

        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            return None

        match = cls.POINTER_PATTERN.match(text)
        if not match:
            return None

        version, oid, size_str = match.groups()
        return cls(oid=oid, size=int(size_str), version=version)

    @classmethod
    def is_pointer(cls, content: bytes) -> bool:
        """Check if content is a valid LFS pointer.

        Args:
            content: Raw file content

        Returns:
            True if content is a valid LFS pointer
        """
        return cls.from_content(content) is not None

    def to_content(self) -> bytes:
        """Generate pointer file content.

        Returns:
            UTF-8 encoded pointer file content
        """
        content = f"version {self.version}\noid sha256:{self.oid}\nsize {self.size}\n"
        return content.encode("utf-8")

    @classmethod
    def create_for_file(cls, file_path: str) -> "LFSPointer":
        """Create LFS pointer for a file.

        Args:
            file_path: Path to the file

        Returns:
            LFSPointer for the file
        """
        file_path_obj = Path(file_path)
        size = file_path_obj.stat().st_size

        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256()
        with file_path_obj.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        return cls(oid=sha256_hash.hexdigest(), size=size)


class LFSManager:
    """Manages Git LFS operations for a repository."""

    def __init__(self, repo_path: str, enabled: bool = True, 
                 size_threshold: float = 100.0, auto_fetch: bool = True, 
                 auto_push: bool = True):
        """Initialize LFS manager.

        Args:
            repo_path: Path to the git repository
            enabled: Whether LFS support is enabled
            size_threshold: Size threshold in MB for using LFS
            auto_fetch: Whether to automatically fetch LFS objects
            auto_push: Whether to automatically push LFS objects
        """
        self.repo_path = Path(repo_path)
        self.lfs_dir = self.repo_path / ".git" / "lfs"
        self.objects_dir = self.lfs_dir / "objects"
        self.enabled = enabled
        self.size_threshold = int(size_threshold * 1024 * 1024)  # Convert MB to bytes
        self.auto_fetch = auto_fetch
        self.auto_push = auto_push

    def is_lfs_enabled(self) -> bool:
        """Check if LFS is enabled for this repository.

        Returns:
            True if LFS is enabled
        """
        if not self.enabled:
            return False
            
        try:
            result = subprocess.run(
                ["git", "lfs", "env"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def get_lfs_object_path(self, oid: str) -> Path:
        """Get the local path for an LFS object.

        Args:
            oid: SHA256 hash of the object

        Returns:
            Path to the LFS object file
        """
        # LFS stores objects in subdirectories based on first 2 chars of OID
        return self.objects_dir / oid[:2] / oid[2:4] / oid

    def has_lfs_object(self, oid: str) -> bool:
        """Check if LFS object exists locally.

        Args:
            oid: SHA256 hash of the object

        Returns:
            True if object exists locally
        """
        return self.get_lfs_object_path(oid).exists()

    def get_lfs_object_content(self, pointer: LFSPointer) -> Optional[bytes]:
        """Get content of an LFS object.

        Args:
            pointer: LFS pointer

        Returns:
            File content if available, None otherwise
        """
        object_path = self.get_lfs_object_path(pointer.oid)
        if not object_path.exists():
            return None

        with object_path.open("rb") as f:
            return f.read()

    def store_lfs_object(self, content: bytes, oid: str) -> None:
        """Store content as an LFS object.

        Args:
            content: File content
            oid: SHA256 hash of the content
        """
        object_path = self.get_lfs_object_path(oid)
        object_path.parent.mkdir(parents=True, exist_ok=True)

        with object_path.open("wb") as f:
            f.write(content)

    def fetch_lfs_objects(self) -> bool:
        """Fetch missing LFS objects from remote.

        Returns:
            True if fetch was successful
        """
        try:
            subprocess.run(
                ["git", "lfs", "fetch"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def push_lfs_objects(self) -> bool:
        """Push LFS objects to remote.

        Returns:
            True if push was successful
        """
        try:
            subprocess.run(
                ["git", "lfs", "push", "--all", "origin"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def should_use_lfs(self, file_path: str, content_size: int) -> bool:
        """Determine if a file should use LFS based on gitattributes and size.

        Args:
            file_path: Path to the file relative to repo root
            content_size: Size of file content in bytes

        Returns:
            True if file should use LFS
        """
        if not self.enabled:
            return False
            
        # Check size threshold first for performance
        if content_size >= self.size_threshold:
            return True
            
        try:
            # Check git attributes for this file
            result = subprocess.run(
                ["git", "check-attr", "filter", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            return "lfs" in result.stdout
        except FileNotFoundError:
            return False

    def get_tracked_patterns(self) -> list[str]:
        """Get LFS tracked file patterns from .gitattributes.

        Returns:
            List of file patterns tracked by LFS
        """
        gitattributes_path = self.repo_path / ".gitattributes"
        if not gitattributes_path.exists():
            return []

        patterns = []
        try:
            with gitattributes_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if " filter=lfs " in line:
                        pattern = line.split()[0]
                        patterns.append(pattern)
        except (OSError, UnicodeDecodeError):
            pass

        return patterns