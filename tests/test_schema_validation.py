import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock the LinkML imports before importing the validate_schema module
sys.modules['linkml_runtime'] = MagicMock()
sys.modules['linkml_runtime.loaders'] = MagicMock()
sys.modules['linkml_runtime.utils'] = MagicMock()
sys.modules['linkml_runtime.utils.schemaview'] = MagicMock()
sys.modules['linkml_runtime.utils.validate_yaml'] = MagicMock()
sys.modules['linkml'] = MagicMock()
sys.modules['linkml.validators'] = MagicMock()
sys.modules['linkml.validators.jsonschemavalidator'] = MagicMock()

# Import the module after mocking
with patch.dict('sys.modules', {
    'linkml_runtime': MagicMock(),
    'linkml_runtime.loaders': MagicMock(),
    'linkml_runtime.loaders.yaml_loader': MagicMock(),
    'linkml_runtime.utils': MagicMock(),
    'linkml_runtime.utils.schemaview': MagicMock(),
    'linkml_runtime.utils.validate_yaml': MagicMock(),
    'linkml': MagicMock(),
    'linkml.validators': MagicMock(),
    'linkml.validators.jsonschemavalidator': MagicMock(),
}):
    import validate_schema
    from validate_schema import validate_schema_file, validate_schema_directory, generate_validation_report


class TestSchemaValidation:
    """Test class for schema validation functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mock objects for testing"""
        # Create mocks for LinkML imports
        self.yaml_loader_mock = MagicMock()
        self.schema_view_mock = MagicMock()
        self.json_validator_mock = MagicMock()
        
        # Apply patches
        with patch('validate_schema.yaml_loader', self.yaml_loader_mock), \
             patch('validate_schema.SchemaView', self.schema_view_mock), \
             patch('validate_schema.JsonSchemaValidator', self.json_validator_mock), \
             patch('validate_schema.logger'):
            yield
    
    def test_validate_schema_file_valid(self, tmp_path):
        """Test validation of a valid schema file."""
        # Create a valid schema file
        valid_schema = tmp_path / "valid_schema.yaml"
        valid_schema.write_text("""
id: https://w3id.org/linkml/tests/valid
name: valid_schema
title: Valid Test Schema

classes:
  TestClass:
    description: A test class
    slots:
      - test_slot

slots:
  test_slot:
    description: A test slot
    range: string
""")
        
        # Configure mocks
        mock_schema = {
            'id': 'https://w3id.org/linkml/tests/valid',
            'name': 'valid_schema',
            'classes': {
                'TestClass': {
                    'slots': ['test_slot']
                }
            },
            'slots': {
                'test_slot': {
                    'range': 'string'
                }
            }
        }
        self.yaml_loader_mock.load.return_value = mock_schema
        
        mock_validation_result = MagicMock()
        mock_validation_result.valid = True
        mock_validation_result.results = []
        self.json_validator_mock.return_value.validate.return_value = mock_validation_result
        
        # Test validation
        with patch('validate_schema.open'), \
             patch('yaml.safe_load', return_value=mock_schema):
            is_valid, errors = validate_schema_file(str(valid_schema))
            assert is_valid
            assert len(errors) == 0
    
    def test_validate_schema_file_invalid(self, tmp_path):
        """Test validation of an invalid schema file."""
        # Create an invalid schema file (missing required fields)
        invalid_schema = tmp_path / "invalid_schema.yaml"
        invalid_schema.write_text("""
# Missing id and name
title: Invalid Test Schema

classes:
  TestClass:
    description: A test class
    slots:
      - nonexistent_slot  # This slot is not defined
""")
        
        # Configure mocks
        mock_schema = {
            'title': 'Invalid Test Schema',
            'classes': {
                'TestClass': {
                    'slots': ['nonexistent_slot']
                }
            },
            # Missing id and name
            # Missing slots section
        }
        self.yaml_loader_mock.load.return_value = mock_schema
        
        # Test validation
        with patch('validate_schema.open'), \
             patch('yaml.safe_load', return_value=mock_schema):
            is_valid, errors = validate_schema_file(str(invalid_schema))
            assert not is_valid
            assert len(errors) > 0
            
    def test_validate_schema_file_not_found(self):
        """Test validation of a non-existent file."""
        with patch('os.path.exists', return_value=False):
            is_valid, errors = validate_schema_file("nonexistent_file.yaml")
            assert not is_valid
            assert "File not found" in errors[0]
    
    def test_validate_schema_directory(self, tmp_path):
        """Test validation of a directory containing schema files."""
        # Create a directory with schema files
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        
        # Add a valid schema
        valid_schema = schema_dir / "valid.yaml"
        valid_schema.write_text("""
id: https://w3id.org/linkml/tests/valid
name: valid_schema
title: Valid Test Schema

classes:
  TestClass:
    description: A test class
    slots:
      - test_slot

slots:
  test_slot:
    description: A test slot
    range: string
""")
        
        # Add an invalid schema
        invalid_schema = schema_dir / "invalid.yaml"
        invalid_schema.write_text("""
# Missing id and name
title: Invalid Test Schema

classes:
  TestClass:
    description: A test class
    slots:
      - nonexistent_slot
""")

        # Mock Path.glob to return our test files
        with patch('pathlib.Path.glob', side_effect=lambda pattern: 
                  [valid_schema, invalid_schema] if pattern.endswith('.yaml') or pattern.endswith('.yml') else []), \
             patch('validate_schema.validate_schema_file') as mock_validate:
            # Configure the mock to return different results for different files
            def validate_side_effect(file_path):
                if str(valid_schema) in file_path:
                    return True, []
                else:
                    return False, ["Error in file"]
            mock_validate.side_effect = validate_side_effect
            
            # Test directory validation
            results = validate_schema_directory(str(schema_dir))
            assert len(results) == 2
            
            # Check that validate_schema_file was called for each file
            assert mock_validate.call_count == 2
    
    def test_generate_validation_report(self, tmp_path):
        """Test generation of a validation report."""
        # Mock validation results
        mock_results = {
            "/path/to/valid.yaml": (True, []),
            "/path/to/invalid1.yaml": (False, ["Error 1", "Error 2"]),
            "/path/to/invalid2.yaml": (False, ["Error 3"])
        }
        
        # Generate report
        report_file = tmp_path / "report.md"
        with patch('builtins.open', create=True):
            report_text = generate_validation_report(mock_results, str(report_file))
        
        # Verify report content
        assert "# LinkML Schema Validation Report" in report_text
        assert "Total schemas validated: 3" in report_text
        assert "Valid schemas: 1" in report_text
        assert "Invalid schemas: 2" in report_text
        assert "Error 1" in report_text
        assert "Error 2" in report_text
        assert "Error 3" in report_text
    
    def test_main_function_file(self, tmp_path):
        """Test the main function with a file argument."""
        valid_schema = tmp_path / "valid.yaml"
        valid_schema.write_text("""
id: https://w3id.org/linkml/tests/valid
name: valid_schema
title: Valid Test Schema

classes:
  TestClass:
    description: A test class
    slots:
      - test_slot

slots:
  test_slot:
    description: A test slot
    range: string
""")
        
        # Test with a valid file
        with patch('sys.argv', ['validate_schema.py', str(valid_schema)]), \
             patch('validate_schema.validate_schema_file', return_value=(True, [])), \
             patch('validate_schema.generate_validation_report'):
            exit_code = validate_schema.main()
            assert exit_code == 0
    
    def test_main_function_directory(self, tmp_path):
        """Test the main function with a directory argument."""
        # Create a directory structure
        schema_dir = tmp_path / "valid_schemas"
        schema_dir.mkdir()
        
        # Test with a directory containing valid schemas
        with patch('sys.argv', ['validate_schema.py', str(schema_dir)]), \
             patch('os.path.isdir', return_value=True), \
             patch('validate_schema.validate_schema_directory', 
                   return_value={"/path/to/valid.yaml": (True, [])}), \
             patch('validate_schema.generate_validation_report'):
            exit_code = validate_schema.main()
            assert exit_code == 0
            
        # Test with a directory containing invalid schemas
        with patch('sys.argv', ['validate_schema.py', str(schema_dir)]), \
             patch('os.path.isdir', return_value=True), \
             patch('validate_schema.validate_schema_directory', 
                   return_value={"/path/to/valid.yaml": (True, []), 
                                 "/path/to/invalid.yaml": (False, ["Error"])}), \
             patch('validate_schema.generate_validation_report'):
            exit_code = validate_schema.main()
            assert exit_code == 1  # Should fail due to invalid schema 