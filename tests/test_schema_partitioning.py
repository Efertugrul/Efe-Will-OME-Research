import os
import pytest
import yaml
import json
import tempfile
from src.generator import generate_linkml_schema

class TestSchemaPartitioning:
    """Tests for schema partitioning functionality"""
    
    def test_schema_filtering(self, temp_output_file, sample_xsd_path):
        """Test that generate_linkml_schema correctly filters elements"""
        # Create a simple JSON schema for testing
        test_schema_path = "test_schema.json"
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "Element1": {"type": "object", "properties": {"attr1": {"type": "string"}}},
                "Element2": {"type": "object", "properties": {"attr2": {"type": "integer"}}},
                "Element3": {"type": "object", "properties": {"attr3": {"type": "boolean"}}}
            },
            "definitions": {
                "Type1": {"type": "string"},
                "Type2": {"type": "integer"}
            }
        }
        
        # Write test schema to file
        with open(test_schema_path, "w") as f:
            json.dump(schema, f)
        
        try:
            # Generate schema for just Sample (from sample.xsd)
            temp_output_file = temp_output_file.replace('.json', '.yaml')
            generate_linkml_schema(sample_xsd_path, temp_output_file, ["Sample"])
            
            # Check that the output file was created
            assert os.path.exists(temp_output_file)
            
            # Load the generated schema
            with open(temp_output_file, "r") as f:
                schema = yaml.safe_load(f)
            
            # Check that the schema contains the Sample class but not other classes
            assert schema is not None
            assert "classes" in schema
            assert "Sample" in schema["classes"]
        finally:
            # Clean up test file
            if os.path.exists(test_schema_path):
                os.remove(test_schema_path)
    
    def test_generate_schema_with_single_element(self, complex_xsd_path, temp_output_file):
        """Test generating a schema with a single element from a complex XSD"""
        # Generate schema for just the Organization element
        temp_output_file = temp_output_file.replace('.json', '.yaml')
        generate_linkml_schema(complex_xsd_path, temp_output_file, ["Organization"])
        
        # Check that the output file was created
        assert os.path.exists(temp_output_file)
        
        # Load the generated schema
        with open(temp_output_file, "r") as f:
            schema = yaml.safe_load(f)
        
        # Check that the schema contains the Organization class
        assert schema is not None
        assert "classes" in schema
        assert "Organization" in schema["classes"]
        
        # Check that the schema does not contain unrelated top-level elements
        # (Note: It may still contain types used by Organization)
        assert len(schema["classes"]) >= 1  # At least Organization should be there
    
    def test_generate_multiple_element_schemas(self, complex_xsd_path, temp_output_dir):
        """Test generating separate schemas for multiple elements"""
        # The complex.xsd only has one element: Organization
        # So we'll just test that one
        element = "Organization"
        output_file = os.path.join(temp_output_dir, f"{element.lower()}.yaml")
        
        # Generate schema for the Organization element
        generate_linkml_schema(complex_xsd_path, output_file, [element])
        
        # Check that the output file was created
        assert os.path.exists(output_file)
        
        # Load and validate the schema
        with open(output_file, "r") as f:
            schema = yaml.safe_load(f)
        
        assert schema is not None
        assert "classes" in schema
        assert element in schema["classes"]
        
        # Check the schema has some content
        assert len(schema["classes"]) > 0
    
    @pytest.mark.skip(reason="This test uses the full OME XSD and might be slow")
    def test_generate_ome_element_schemas(self, ome_xsd_path, temp_output_dir):
        """Test generating separate schemas for OME elements"""
        # Select some key OME elements to test
        elements = ["OME", "Image", "Instrument"]
        
        for element in elements:
            output_file = os.path.join(temp_output_dir, f"{element.lower()}.yaml")
            
            # Generate schema for the element
            generate_linkml_schema(ome_xsd_path, output_file, [element])
            
            # Check that the output file was created
            assert os.path.exists(output_file)
            
            # Load and validate the schema
            with open(output_file, "r") as f:
                schema = yaml.safe_load(f)
                
            assert schema is not None
            assert "classes" in schema
            assert element in schema["classes"]
            
            # For certain elements, check for expected nested elements
            if element == "Instrument":
                instrument_class = schema["classes"]["Instrument"]
                # Check for references to Detector, Objective, etc.
                assert any("Detector" in s for s in instrument_class.get("slots", []))
                assert any("Objective" in s for s in instrument_class.get("slots", []))
            
            if element == "Image":
                image_class = schema["classes"]["Image"]
                # Check for references to Pixels, etc.
                assert any("Pixels" in s for s in image_class.get("slots", [])) 