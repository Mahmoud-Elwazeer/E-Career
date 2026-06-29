"""
CV file processing and text extraction
"""

import os
import logging
from pathlib import Path
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)


class CVParser:
    """Extract text from CV files (PDF, DOCX, TXT)"""

    SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.txt']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @classmethod
    def extract_text(cls, file: UploadedFile) -> str:
        """
        Extract text from uploaded CV file

        Args:
            file: Django UploadedFile instance

        Returns:
            str: Extracted text content

        Raises:
            ValueError: If file format not supported or file too large
        """
        # Validate file size
        if file.size > cls.MAX_FILE_SIZE:
            raise ValueError(f"File too large. Maximum size is {cls.MAX_FILE_SIZE / 1024 / 1024}MB")

        # Get file extension
        file_ext = Path(file.name).suffix.lower()

        if file_ext not in cls.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format. Supported: {', '.join(cls.SUPPORTED_FORMATS)}")

        # Extract text based on format
        try:
            if file_ext == '.pdf':
                return cls._extract_from_pdf(file)
            elif file_ext in ['.docx', '.doc']:
                return cls._extract_from_docx(file)
            elif file_ext == '.txt':
                return cls._extract_from_txt(file)
        except Exception as e:
            logger.error(f"Error extracting text from {file.name}: {e}")
            raise ValueError(f"Failed to extract text from file: {str(e)}")

    @staticmethod
    def _extract_from_pdf(file: UploadedFile) -> str:
        """Extract text from PDF"""
        try:
            import PyPDF2
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF extraction. Install with: pip install PyPDF2")

        text = []

        pdf_reader = PyPDF2.PdfReader(file)

        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)

        return '\n\n'.join(text)

    @staticmethod
    def _extract_from_docx(file: UploadedFile) -> str:
        """Extract text from DOCX"""
        try:
            import docx
        except ImportError:
            raise ImportError("python-docx is required for DOCX extraction. Install with: pip install python-docx")

        doc = docx.Document(file)

        text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text)

        return '\n\n'.join(text)

    @staticmethod
    def _extract_from_txt(file: UploadedFile) -> str:
        """Extract text from TXT"""
        try:
            return file.read().decode('utf-8')
        except UnicodeDecodeError:
            # Try other encodings
            file.seek(0)
            return file.read().decode('latin-1')

    @classmethod
    def get_file_info(cls, file: UploadedFile) -> dict:
        """
        Get information about uploaded file

        Args:
            file: Django UploadedFile instance

        Returns:
            dict: File information
        """
        file_ext = Path(file.name).suffix.lower()

        return {
            'name': file.name,
            'size': file.size,
            'extension': file_ext,
            'is_supported': file_ext in cls.SUPPORTED_FORMATS,
            'size_mb': round(file.size / (1024 * 1024), 2)
        }