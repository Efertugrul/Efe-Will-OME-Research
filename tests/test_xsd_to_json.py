import os
import json
import pytest
import xmlschema
from src.xsdtojson import xsd_to_json_schema
import tempfile
import sys
from unittest.mock import patch, MagicMock

class TestXsdToJson:
    """Tests for the xsd_to_json_schema function"""
    
    def test_xsd_to_json_schema_sample(self, sample_xsd_path):
        """Test converting a simple XSD to JSON Schema"""
        # Convert XSD to JSON Schema
        json_schema = xsd_to_json_schema(sample_xsd_path)
        
        # Check the returned schema
        assert json_schema is not None
        assert "$schema" in json_schema
        assert "properties" in json_schema
        assert "Sample" in json_schema["properties"]
    
    def test_xsd_to_json_schema_complex(self, complex_xsd_path):
        """Test converting a complex XSD to JSON Schema"""
        # Convert XSD to JSON Schema
        json_schema = xsd_to_json_schema(complex_xsd_path)
        
        # Check the returned schema
        assert json_schema is not None
        assert "$schema" in json_schema
        assert "properties" in json_schema
        assert "Organization" in json_schema["properties"]
    
    def test_xsd_to_json_schema_nonexistent_file(self):
        """Test error handling for a nonexistent XSD file"""
        with pytest.raises(Exception):
            xsd_to_json_schema("nonexistent.xsd")
    
    def test_xsd_to_json_schema_invalid_xml(self):
        """Test error handling for an invalid XML file"""
        # Create a file with invalid XML
        invalid_xml_path = "invalid.xml"
        with open(invalid_xml_path, "w") as f:
            f.write("<invalid>xml<unclosed>")
        
        try:
            with pytest.raises(Exception):
                xsd_to_json_schema(invalid_xml_path)
        finally:
            # Clean up
            if os.path.exists(invalid_xml_path):
                os.remove(invalid_xml_path)
    
    def test_xsd_to_json_schema_serializable(self, sample_xsd_path):
        """Test that the returned JSON Schema is serializable"""
        # Convert XSD to JSON Schema
        json_schema = xsd_to_json_schema(sample_xsd_path)
        
        # Attempt to serialize the schema to JSON
        json_str = json.dumps(json_schema)
        
        # Check that the serialized schema is valid JSON
        assert json_str is not None
        assert len(json_str) > 0
        
        # Check that the serialized schema can be parsed back to the original schema
        parsed_schema = json.loads(json_str)
        assert parsed_schema == json_schema

    @patch('argparse.ArgumentParser.parse_args')
    @patch('builtins.print')
    def test_main_without_output(self, mock_print, mock_args, sample_xsd_path):
        """Test the command-line interface without an output file"""
        # Set up mock args to simulate command line arguments
        mock_args.return_value = MagicMock(
            input_file=sample_xsd_path,
            output=None
        )
        
        # Directly call the main function
        from src.xsdtojson import main
        main()
        
        # Check that print was called
        mock_print.assert_called()
        
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_with_output_file(self, mock_args, sample_xsd_path):
        """Test the command-line interface with an output file"""
        # Create a temporary output file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            output_path = temp_file.name
        
        try:
            # Set up mock args to simulate command line arguments
            mock_args.return_value = MagicMock(
                input_file=sample_xsd_path,
                output=output_path
            )
            
            # Directly call the main function
            from src.xsdtojson import main
            main()
            
            # Check that the output file was created
            assert os.path.exists(output_path)
            
            # Check the contents of the output file
            with open(output_path, 'r') as f:
                json_obj = json.load(f)
            
            assert json_obj is not None
            assert "$schema" in json_obj
            assert "properties" in json_obj
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.remove(output_path) 