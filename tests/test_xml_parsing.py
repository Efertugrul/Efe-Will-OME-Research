import os
import pytest
import xmlschema
from xsdata.exceptions import ParserError

class TestXmlParsing:
    """Tests for XML Schema parsing with xmlschema"""

    def test_parse_sample_xsd(self, sample_xsd_path):
        """Test parsing a simple sample XSD file"""
        # Parse the XSD file
        schema = xmlschema.XMLSchema(sample_xsd_path)
        
        # Check that the schema was created
        assert schema is not None
        
        # Check the target namespace
        assert schema.target_namespace == "http://www.example.org/sample"
        
        # Check that the element was parsed
        assert "Sample" in schema.elements
        sample_element = schema.elements["Sample"]
        assert sample_element.local_name == "Sample"
        
        # Just check the schema validation works
        assert schema.is_valid("<sample:Sample id='sample1' xmlns:sample='http://www.example.org/sample'><sample:Name>Test</sample:Name><sample:Value>123</sample:Value></sample:Sample>")

    def test_parse_complex_xsd(self, complex_xsd_path):
        """Test parsing a complex XSD file with inheritance and references"""
        # Parse the XSD file
        schema = xmlschema.XMLSchema(complex_xsd_path)
        
        # Check that the schema was created
        assert schema is not None
        
        # Check the target namespace
        assert schema.target_namespace == "http://www.example.org/complex"
        
        # Check complex type definitions
        assert "ResourceType" in schema.types
        assert "PersonType" in schema.types
        assert "ProjectType" in schema.types
        
        # Check that the Organization element was parsed
        assert "Organization" in schema.elements
        org_element = schema.elements["Organization"]
        assert org_element.local_name == "Organization"

    def test_parse_ome_xsd(self, ome_xsd_path):
        """Test parsing the OME XSD file"""
        try:
            # Parse the XSD file
            schema = xmlschema.XMLSchema(ome_xsd_path)
            
            # Check that the schema was created
            assert schema is not None
            
            # Check the target namespace
            assert schema.target_namespace == "http://www.openmicroscopy.org/Schemas/OME/2016-06"
            
            # Check that the main OME element was parsed
            assert "OME" in schema.elements
            ome_element = schema.elements["OME"]
            assert ome_element.local_name == "OME"
            
            # Check for some known elements in the OME schema
            schema_elements = list(schema.elements.keys())
            expected_elements = ["OME", "Image", "Instrument", "ROI"]
            for element in expected_elements:
                assert element in schema_elements
            
        except Exception as e:
            pytest.fail(f"Failed to parse OME XSD: {str(e)}")

    def test_error_handling_nonexistent_file(self):
        """Test that parsing a nonexistent file raises an appropriate error"""
        with pytest.raises(Exception):
            xmlschema.XMLSchema("nonexistent_file.xsd")

    def test_error_handling_invalid_xml(self, temp_output_dir):
        """Test that parsing an invalid XML file raises an appropriate error"""
        # Create an invalid XML file
        invalid_xml_path = os.path.join(temp_output_dir, "invalid.xsd")
        with open(invalid_xml_path, "w") as f:
            f.write("This is not valid XML or XSD content")
        
        with pytest.raises(Exception):
            xmlschema.XMLSchema(invalid_xml_path) 