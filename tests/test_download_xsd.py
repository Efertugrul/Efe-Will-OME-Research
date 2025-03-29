import os
import pytest
import requests
import tempfile
from unittest.mock import patch, MagicMock
from src.download_xsd import download_xsd, OME_XSD_URL

class TestDownloadXsd:
    """Tests for download_xsd.py module"""
    
    @patch('src.download_xsd.requests.get')
    def test_download_xsd(self, mock_get):
        """Test downloading an XSD file"""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.content = b"<xml>Test XSD content</xml>"
        mock_get.return_value = mock_response
        
        # Call download_xsd with a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            download_xsd("https://example.com/test.xsd", temp_path)
            
            # Check that the file was created
            assert os.path.exists(temp_path)
            
            # Check file contents
            with open(temp_path, "rb") as f:
                content = f.read()
                assert content == b"<xml>Test XSD content</xml>"
            
            # Verify requests.get was called with the correct URL
            mock_get.assert_called_once_with("https://example.com/test.xsd")
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @patch('src.download_xsd.requests.get')
    def test_download_xsd_error(self, mock_get):
        """Test error handling during download"""
        # Create a mock response with an error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        # Call download_xsd with a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            # Check that the error is propagated
            with pytest.raises(requests.exceptions.HTTPError):
                download_xsd("https://example.com/nonexistent.xsd", temp_path)
                
            # Verify requests.get was called with the correct URL
            mock_get.assert_called_once_with("https://example.com/nonexistent.xsd")
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_ome_xsd_url_format(self):
        """Test that the OME XSD URL is correctly formatted"""
        assert OME_XSD_URL.startswith("https://")
        assert OME_XSD_URL.endswith(".xsd")
        assert "openmicroscopy.org" in OME_XSD_URL 