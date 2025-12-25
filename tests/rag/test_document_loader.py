"""
Tests for document_loader.py - Document reading functions.

This module tests:
- determine_encoding: Detect file encoding
- read_txt_to_string: Read text files
- read_pdf_to_string: Read PDF files
- read_docx_to_string: Read DOCX files
"""
import pytest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)


class TestDetermineEncoding:
    """Tests for the determine_encoding function."""
    
    def test_determine_encoding_utf8(self, temp_txt_file):
        """Test detecting UTF-8 encoding."""
        from src.rag.document_loader import determine_encoding
        
        encoding = determine_encoding(temp_txt_file)
        # chardet typically detects UTF-8 or ascii for simple English text
        assert encoding is not None
        assert encoding.lower() in ['utf-8', 'ascii', 'iso-8859-1']
    
    @patch('builtins.open', mock_open(read_data=b'\xff\xfe\x00\x00'))
    @patch('chardet.detect')
    def test_determine_encoding_with_bom(self, mock_chardet):
        """Test encoding detection with BOM markers."""
        mock_chardet.return_value = {'encoding': 'UTF-32-LE'}
        
        from src.rag.document_loader import determine_encoding
        
        encoding = determine_encoding('dummy_path')
        assert encoding == 'UTF-32-LE'
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_determine_encoding_file_not_found(self, mock_file):
        """Test handling of non-existent file."""
        from src.rag.document_loader import determine_encoding
        
        with pytest.raises(FileNotFoundError):
            determine_encoding('non_existent_file.txt')


class TestReadTxtToString:
    """Tests for the read_txt_to_string function."""
    
    def test_read_txt_to_string_success(self, temp_txt_file):
        """Test successful reading of a text file."""
        from src.rag.document_loader import read_txt_to_string
        
        content = read_txt_to_string(temp_txt_file)
        
        assert content is not None
        assert "This is test content" in content
        assert "Second line" in content
    
    @patch('src.rag.document_loader.TextLoader')
    @patch('src.rag.document_loader.determine_encoding')
    def test_read_txt_to_string_with_mock(self, mock_encoding, mock_loader):
        """Test reading text file with mocked dependencies."""
        mock_encoding.return_value = 'utf-8'
        
        mock_doc = MagicMock()
        mock_doc.page_content = "Mocked content from text file"
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.return_value = [mock_doc]
        mock_loader.return_value = mock_loader_instance
        
        from src.rag.document_loader import read_txt_to_string
        
        content = read_txt_to_string('dummy_path.txt')
        
        assert content == "Mocked content from text file"
        mock_loader.assert_called_once()
    
    def test_read_txt_to_string_empty_file(self, tmp_path):
        """Test reading an empty text file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("", encoding='utf-8')
        
        from src.rag.document_loader import read_txt_to_string
        
        content = read_txt_to_string(str(empty_file))
        assert content == ""


class TestReadPdfToString:
    """Tests for the read_pdf_to_string function."""
    
    @patch('src.rag.document_loader.PyPDFLoader')
    def test_read_pdf_to_string_success(self, mock_loader, tmp_path):
        """Test successful reading of a PDF file."""
        # Create mock documents for multiple pages
        mock_docs = [
            MagicMock(page_content="Page 1 content"),
            MagicMock(page_content="Page 2 content"),
            MagicMock(page_content="Page 3 content")
        ]
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.return_value = mock_docs
        mock_loader.return_value = mock_loader_instance
        
        from src.rag.document_loader import read_pdf_to_string
        
        # Create a temp file path
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        
        content = read_pdf_to_string(str(pdf_path))
        
        assert "Page 1 content" in content
        assert "Page 2 content" in content
        assert "Page 3 content" in content
    
    @patch('src.rag.document_loader.PyPDFLoader')
    def test_read_pdf_to_string_single_page(self, mock_loader, tmp_path):
        """Test reading a single-page PDF."""
        mock_doc = MagicMock(page_content="Single page content")
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.return_value = [mock_doc]
        mock_loader.return_value = mock_loader_instance
        
        from src.rag.document_loader import read_pdf_to_string
        
        pdf_path = tmp_path / "single_page.pdf"
        pdf_path.touch()
        
        content = read_pdf_to_string(str(pdf_path))
        
        assert "Single page content" in content
    
    @patch('src.rag.document_loader.PyPDFLoader')
    def test_read_pdf_to_string_empty_pdf(self, mock_loader, tmp_path):
        """Test reading an empty PDF."""
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.return_value = []
        mock_loader.return_value = mock_loader_instance
        
        from src.rag.document_loader import read_pdf_to_string
        
        pdf_path = tmp_path / "empty.pdf"
        pdf_path.touch()
        
        content = read_pdf_to_string(str(pdf_path))
        
        assert content == ""


class TestReadDocxToString:
    """Tests for the read_docx_to_string function."""
    
    @patch('src.rag.document_loader.Docx2txtLoader')
    def test_read_docx_to_string_success(self, mock_loader):
        """Test successful reading of a DOCX file."""
        mock_doc = MagicMock()
        mock_doc.page_content = "DOCX document content with formatted text"
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.return_value = [mock_doc]
        mock_loader.return_value = mock_loader_instance
        
        from src.rag.document_loader import read_docx_to_string
        
        content = read_docx_to_string('dummy_path.docx')
        
        assert content == "DOCX document content with formatted text"
        mock_loader.assert_called_once_with('dummy_path.docx')
    
    @patch('src.rag.document_loader.Docx2txtLoader')
    def test_read_docx_to_string_complex_document(self, mock_loader):
        """Test reading a complex DOCX with multiple sections."""
        mock_doc = MagicMock()
        mock_doc.page_content = """
        Title: Test Document
        
        Section 1: Introduction
        This is the introduction section.
        
        Section 2: Content
        This is the main content.
        """
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.return_value = [mock_doc]
        mock_loader.return_value = mock_loader_instance
        
        from src.rag.document_loader import read_docx_to_string
        
        content = read_docx_to_string('complex.docx')
        
        assert "Title: Test Document" in content
        assert "Section 1: Introduction" in content
        assert "Section 2: Content" in content


class TestDocumentLoaderIntegration:
    """Integration tests for document loader functions."""
    
    def test_multiple_txt_files(self, tmp_path):
        """Test reading multiple text files."""
        from src.rag.document_loader import read_txt_to_string
        
        files = []
        for i in range(3):
            file_path = tmp_path / f"file_{i}.txt"
            file_path.write_text(f"Content of file {i}", encoding='utf-8')
            files.append(str(file_path))
        
        contents = [read_txt_to_string(f) for f in files]
        
        assert len(contents) == 3
        for i, content in enumerate(contents):
            assert f"Content of file {i}" in content
    
    def test_file_with_unicode(self, tmp_path):
        """Test reading files with unicode content."""
        from src.rag.document_loader import read_txt_to_string
        
        unicode_file = tmp_path / "unicode.txt"
        unicode_content = "Unicode: こんにちは, مرحبا, 你好"
        unicode_file.write_text(unicode_content, encoding='utf-8')
        
        content = read_txt_to_string(str(unicode_file))
        
        # Content should be readable (encoding detected)
        assert content is not None
