"""
Tests for the CV parser system.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.profiles.cv_parser import (
    CVParser,
    ResumeParserPlugin,
    DoclingParserPlugin,
    PdfplumberParserPlugin,
    EasyOCRParserPlugin,
    DocxParserPlugin,
    TxtParserPlugin,
    ParsedCVData,
)


class TestResumeParserPlugin(TestCase):
    """Test the ResumeParserPlugin interface."""
    
    def test_plugin_is_abstract(self):
        """Test that ResumeParserPlugin is an abstract base class."""
        with pytest.raises(TypeError):
            ResumeParserPlugin()


class TestDoclingParserPlugin(TestCase):
    """Test the Docling parser plugin."""
    
    def setUp(self):
        self.parser = DoclingParserPlugin()
    
    def test_can_handle_pdf(self):
        """Test that Docling can handle PDF files."""
        assert self.parser.can_handle("test.pdf", "pdf") is True
    
    def test_can_handle_non_pdf(self):
        """Test that Docling cannot handle non-PDF files."""
        assert self.parser.can_handle("test.txt", "txt") is False
    
    def test_name_property(self):
        """Test that the name property returns 'docling'."""
        assert self.parser.name == "docling"


class TestPdfplumberParserPlugin(TestCase):
    """Test the pdfplumber parser plugin."""
    
    def setUp(self):
        self.parser = PdfplumberParserPlugin()
    
    def test_can_handle_pdf(self):
        """Test that pdfplumber can handle PDF files."""
        assert self.parser.can_handle("test.pdf", "pdf") is True
    
    def test_name_property(self):
        """Test that the name property returns 'pdfplumber'."""
        assert self.parser.name == "pdfplumber"


class TestEasyOCRParserPlugin(TestCase):
    """Test the EasyOCR parser plugin."""
    
    def setUp(self):
        self.parser = EasyOCRParserPlugin()
    
    def test_can_handle_image_files(self):
        """Test that EasyOCR can handle image files."""
        assert self.parser.can_handle("test.png", "png") is True
        assert self.parser.can_handle("test.jpg", "jpg") is True
    
    def test_can_handle_pdf(self):
        """Test that EasyOCR can handle PDF files."""
        assert self.parser.can_handle("test.pdf", "pdf") is True
    
    def test_name_property(self):
        """Test that the name property returns 'easyocr'."""
        assert self.parser.name == "easyocr"


class TestDocxParserPlugin(TestCase):
    """Test the DOCX parser plugin."""
    
    def setUp(self):
        self.parser = DocxParserPlugin()
    
    def test_can_handle_docx(self):
        """Test that DOCX parser can handle DOCX files."""
        assert self.parser.can_handle("test.docx", "docx") is True
    
    def test_can_handle_doc(self):
        """Test that DOCX parser can handle DOC files."""
        assert self.parser.can_handle("test.doc", "doc") is True
    
    def test_name_property(self):
        """Test that the name property returns 'docx'."""
        assert self.parser.name == "docx"


class TestTxtParserPlugin(TestCase):
    """Test the TXT parser plugin."""
    
    def setUp(self):
        self.parser = TxtParserPlugin()
    
    def test_can_handle_txt(self):
        """Test that TXT parser can handle TXT files."""
        assert self.parser.can_handle("test.txt", "txt") is True
    
    def test_name_property(self):
        """Test that the name property returns 'txt'."""
        assert self.parser.name == "txt"


class TestCVParser(TestCase):
    """Test the main CV parser."""
    
    def setUp(self):
        self.parser = CVParser()
    
    def test_supported_formats(self):
        """Test that all expected formats are supported."""
        expected_formats = [
            '.pdf', '.docx', '.doc', '.txt', 
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'
        ]
        assert self.parser.SUPPORTED_FORMATS == expected_formats
    
    def test_max_file_size(self):
        """Test that max file size is 10MB."""
        assert self.parser.MAX_FILE_SIZE == 10 * 1024 * 1024
    
    def test_get_file_type(self):
        """Test file type detection."""
        assert self.parser._get_file_type("test.pdf") == "pdf"
        assert self.parser._get_file_type("test.docx") == "docx"
        assert self.parser._get_file_type("test.txt") == "txt"
    
    def test_find_parser(self):
        """Test parser selection."""
        parser = self.parser._find_parser("test.pdf", "pdf")
        assert parser is not None
        assert parser.name in ["docling", "pdfplumber"]
    
    def test_get_file_info(self):
        """Test file info extraction."""
        # Create a mock file
        content = b"test content"
        mock_file = SimpleUploadedFile("test.pdf", content, content_type="application/pdf")
        mock_file.size = len(content)
        
        info = self.parser.get_file_info(mock_file)
        assert info['name'] == "test.pdf"
        assert info['size'] == len(content)
        assert info['extension'] == ".pdf"
        assert info['is_supported'] is True
        assert info['size_mb'] == round(len(content) / (1024 * 1024), 2)


class TestParsedCVData(TestCase):
    """Test the ParsedCVData dataclass."""
    
    def test_default_values(self):
        """Test that ParsedCVData has correct default values."""
        data = ParsedCVData()
        
        assert data.personal == {}
        assert data.experience == []
        assert data.education == []
        assert data.skills == {}
        assert data.certifications == []
        assert data.projects == []
        assert data.raw_text == ""
        assert data.parser_used == ""
    
    def test_custom_values(self):
        """Test that ParsedCVData can be initialized with custom values."""
        data = ParsedCVData(
            personal={"name": "John Doe"},
            experience=[{"title": "Software Engineer"}],
            parser_used="docling"
        )
        
        assert data.personal == {"name": "John Doe"}
        assert data.experience == [{"title": "Software Engineer"}]
        assert data.parser_used == "docling"