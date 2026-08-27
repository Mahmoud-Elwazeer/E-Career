"""
Upload Security Module

Provides defense-in-depth file validation:
1. Extension whitelist
2. File size limits
3. Magic byte (content-type) verification
4. Filename sanitization
5. Path traversal prevention
"""
import os
import re
import logging
from typing import Optional, Set, Tuple

logger = logging.getLogger(__name__)

MAGIC_BYTES = {
    b'%PDF': {'.pdf'},
    b'PK\x03\x04': {'.docx', '.xlsx', '.pptx', '.zip'},
    b'\xd0\xcf\x11\xe0': {'.doc', '.xls', '.ppt'},
    b'\x89PNG': {'.png'},
    b'\xff\xd8\xff': {'.jpg', '.jpeg'},
    b'GIF87a': {'.gif'},
    b'GIF89a': {'.gif'},
    b'II\x2a\x00': {'.tiff', '.tif'},
    b'MM\x00\x2a': {'.tiff', '.tif'},
    b'BM': {'.bmp'},
}

DEFAULT_ALLOWED_EXTENSIONS: Set[str] = {
    '.pdf', '.docx', '.doc', '.txt',
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif',
}

DEFAULT_MAX_SIZE = 10 * 1024 * 1024  # 10MB


class UploadValidator:
    """Validates uploaded files for security."""

    def __init__(
        self,
        allowed_extensions: Optional[Set[str]] = None,
        max_size: int = DEFAULT_MAX_SIZE,
    ):
        self.allowed_extensions = allowed_extensions or DEFAULT_ALLOWED_EXTENSIONS
        self.max_size = max_size

    def validate(self, file) -> Tuple[bool, Optional[str]]:
        """
        Validate an uploaded file. Returns (is_valid, error_message).
        """
        # 1. Filename sanitization + extension check
        filename = self.sanitize_filename(file.name)
        ext = os.path.splitext(filename)[1].lower()

        if ext not in self.allowed_extensions:
            return False, f"File type '{ext}' not allowed. Permitted: {', '.join(sorted(self.allowed_extensions))}"

        # 2. Size check
        if file.size > self.max_size:
            max_mb = self.max_size / (1024 * 1024)
            return False, f"File too large ({file.size / (1024*1024):.1f}MB). Maximum: {max_mb:.0f}MB"

        # 3. Magic byte verification (skip for .txt)
        if ext != '.txt':
            if not self._verify_magic_bytes(file, ext):
                return False, "File content does not match its extension (possible spoofing attempt)"

        # 4. Path traversal check
        if '..' in file.name or '/' in file.name or '\\' in file.name:
            return False, "Invalid filename (path traversal attempt detected)"

        return True, None

    def sanitize_filename(self, filename: str) -> str:
        """Remove dangerous characters from filename."""
        filename = os.path.basename(filename)
        filename = re.sub(r'[^\w\s\-.]', '', filename)
        filename = re.sub(r'\s+', '_', filename)
        if not filename or filename.startswith('.'):
            filename = 'upload' + filename
        return filename[:255]

    def _verify_magic_bytes(self, file, expected_ext: str) -> bool:
        """Check that file's magic bytes match its claimed extension."""
        try:
            pos = file.tell()
            header = file.read(8)
            file.seek(pos)

            if not header:
                return False

            for magic, extensions in MAGIC_BYTES.items():
                if header.startswith(magic):
                    return expected_ext in extensions

            # If no magic match found but it's a known binary format, reject
            # For text-like formats (.txt, unknown), allow
            if expected_ext in {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.doc'}:
                return False

            # .docx is a ZIP, already covered by PK magic bytes
            return True

        except Exception as e:
            logger.warning("Magic byte check failed: %s", e)
            return True  # Allow on error (fail open for availability)


upload_validator = UploadValidator()
