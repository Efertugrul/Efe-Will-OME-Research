import os
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Create all the necessary mock classes for LinkML imports
yaml_loader_mock = MagicMock()
schema_view_mock = MagicMock()
json_validator_mock = MagicMock()

# Mock the entire validate_yaml module
class MockValidateYaml:
    @staticmethod
    def validate_yaml(*args, **kwargs):
        return True

# Mock the entire module structure
sys.modules['linkml_runtime'] = MagicMock()
sys.modules['linkml_runtime.loaders'] = MagicMock()
sys.modules['linkml_runtime.loaders.yaml_loader'] = yaml_loader_mock
sys.modules['linkml_runtime.utils'] = MagicMock()
sys.modules['linkml_runtime.utils.schemaview'] = MagicMock()
sys.modules['linkml_runtime.utils.validate_yaml'] = MockValidateYaml()
sys.modules['linkml'] = MagicMock()
sys.modules['linkml.validators'] = MagicMock()
sys.modules['linkml.validators.jsonschemavalidator'] = MagicMock()
sys.modules['linkml.utils'] = MagicMock()
sys.modules['linkml.utils.validate_yaml'] = MockValidateYaml()

# Import the module after mocking
import validate_schema
from validate_schema import validate_schema_file, validate_schema_directory, generate_validation_report

# Override the imported modules with our mocks for consistent testing
validate_schema.yaml_loader = yaml_loader_mock
validate_schema.SchemaView = schema_view_mock
validate_schema.JsonSchemaValidator = json_validator_mock
validate_schema.linkml_imports_ok = True

class TestSchemaValidation:
    """Test class for schema validation functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mock objects for testing"""
        # Reset mocks before each test
        yaml_loader_mock.reset_mock()
        schema_view_mock.reset_mock()
        json_validator_mock.reset_mock()
        
        # Configure default values
        mock_validation_result = MagicMock()
        mock_validation_result.valid = True
        mock_validation_result.results = []
        json_validator_mock.return_value.validate.return_value = mock_validation_result
        
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
        
        # Configure the mock schema
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
        
        # Set up mocks to return our schema
        yaml_loader_mock.load.return_value = mock_schema
        schema_view_mock.return_value = MagicMock()
        
        # Mock the YAML loading
        mock_yaml_load = MagicMock(return_value=mock_schema)
        
        # Test validation
        with patch('os.path.exists', return_value=True), \
             patch('yaml.safe_load', mock_yaml_load), \
             patch('builtins.open', mock_open(read_data="")), \
             patch('validate_schema.JsonSchemaValidator', return_value=json_validator_mock.return_value):
            
            is_valid, errors = validate_schema_file(str(valid_schema))
            
            # Verify the results
            assert is_valid is True
            assert len(errors) == 0
            
            # Verify that our mocks were called correctly
            assert yaml_loader_mock.load.called
    
    def test_validate_schema_file_invalid(self, tmp_path):
        """Test validation of an invalid schema file."""
        # Create an invalid schema file
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
        
        # Configure the mock schema
        mock_schema = {
            'title': 'Invalid Test Schema',
            'classes': {
                'TestClass': {
                    'slots': ['nonexistent_slot']
                }
            }
            # Missing id and name
            # Missing slots section
        }
        
        # Set up mocks to return our schema
        yaml_loader_mock.load.return_value = mock_schema
        schema_view_mock.return_value = MagicMock()
        
        # Test validation
        with patch('os.path.exists', return_value=True), \
             patch('yaml.safe_load', return_value=mock_schema), \
             patch('builtins.open', mock_open(read_data="")), \
             patch('validate_schema.JsonSchemaValidator', return_value=json_validator_mock.return_value):
            
            is_valid, errors = validate_schema_file(str(invalid_schema))
            
            # Verify the results
            assert is_valid is False
            assert len(errors) > 0
            
            # Ensure we found the expected errors
            id_error = any("Missing 'id'" in error for error in errors)
            name_error = any("Missing 'name'" in error for error in errors)
            assert id_error and name_error
            
    def test_validate_schema_file_not_found(self):
        """Test validation of a non-existent file."""
        with patch('os.path.exists', return_value=False):
            is_valid, errors = validate_schema_file("nonexistent_file.yaml")
            assert is_valid is False
            assert "File not found" in errors[0]
    
    def test_validate_schema_directory(self, tmp_path):
        """Test validation of a directory containing schema files."""
        # Create a directory with schema files
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        
        # Add a valid schema
        valid_schema = schema_dir / "valid.yaml"
        valid_schema.write_text("valid schema content")
        
        # Add an invalid schema
        invalid_schema = schema_dir / "invalid.yaml"
        invalid_schema.write_text("invalid schema content")

        # Create mocked path objects and validation results
        mock_valid_path = MagicMock()
        mock_valid_path.__str__.return_value = str(valid_schema)
        
        mock_invalid_path = MagicMock()
        mock_invalid_path.__str__.return_value = str(invalid_schema)
        
        # We need to patch the actual functions being called in the implementation
        with patch('validate_schema.logger'), \
             patch('pathlib.Path.glob', return_value=[valid_schema, invalid_schema]), \
             patch('validate_schema.validate_schema_file', autospec=True) as mock_validate:
            
            # Configure mock_validate to return different results based on file
            def validate_side_effect(file_path, verbose=False):
                if str(valid_schema) in file_path:
                    return True, []
                else:
                    return False, ["Error in invalid schema"]
            mock_validate.side_effect = validate_side_effect
            
            # Test directory validation
            results = validate_schema_directory(str(schema_dir))
            
            # Verify results
            assert len(results) == 2
            
            # Just verify that the mock was called, instead of counting
            assert mock_validate.called
            
            # Check for expected keys in results
            assert str(valid_schema) in results
            assert str(invalid_schema) in results
            
            # Check the validation results
            assert results[str(valid_schema)][0] is True
            assert results[str(invalid_schema)][0] is False
    
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
        with patch('builtins.open', mock_open()) as mock_file:
            report_text = generate_validation_report(mock_results, str(report_file))
        
        # Verify report content
        assert "# LinkML Schema Validation Report" in report_text
        assert "Total schemas validated: 3" in report_text
        assert "Valid schemas: 1" in report_text
        assert "Invalid schemas: 2" in report_text
        assert "Error 1" in report_text
        assert "Error 2" in report_text
        assert "Error 3" in report_text
        
        # Verify file was written to
        mock_file.assert_called_once_with(str(report_file), 'w')
    
    def test_main_function_file(self, tmp_path):
        """Test the main function with a file argument."""
        valid_schema = tmp_path / "valid.yaml"
        valid_schema.write_text("""valid schema content""")
        
        # Test with a valid file
        with patch('sys.argv', ['validate_schema.py', str(valid_schema)]), \
             patch('os.path.isfile', return_value=True), \
             patch('os.path.isdir', return_value=False), \
             patch('validate_schema.validate_schema_file', return_value=(True, [])), \
             patch('validate_schema.generate_validation_report'):
            exit_code = validate_schema.main()
            assert exit_code == 0
        
        # Test with an invalid file
        with patch('sys.argv', ['validate_schema.py', str(valid_schema)]), \
             patch('os.path.isfile', return_value=True), \
             patch('os.path.isdir', return_value=False), \
             patch('validate_schema.validate_schema_file', return_value=(False, ["Error"])), \
             patch('validate_schema.generate_validation_report'):
            exit_code = validate_schema.main()
            assert exit_code == 1
    
    def test_main_function_directory(self, tmp_path):
        """Test the main function with a directory argument."""
        # Create a directory structure
        schema_dir = tmp_path / "valid_schemas"
        schema_dir.mkdir()
        
        # Test with a directory containing valid schemas
        with patch('sys.argv', ['validate_schema.py', str(schema_dir)]), \
             patch('os.path.isfile', return_value=False), \
             patch('os.path.isdir', return_value=True), \
             patch('validate_schema.validate_schema_directory', 
                   return_value={"/path/to/valid.yaml": (True, [])}), \
             patch('validate_schema.generate_validation_report'):
            exit_code = validate_schema.main()
            assert exit_code == 0
            
        # Test with a directory containing invalid schemas
        with patch('sys.argv', ['validate_schema.py', str(schema_dir)]), \
             patch('os.path.isfile', return_value=False), \
             patch('os.path.isdir', return_value=True), \
             patch('validate_schema.validate_schema_directory', 
                   return_value={"/path/to/valid.yaml": (True, []), 
                                 "/path/to/invalid.yaml": (False, ["Error"])}), \
             patch('validate_schema.generate_validation_report'):
            exit_code = validate_schema.main()
            assert exit_code == 1
            
        # Test with an empty directory
        with patch('sys.argv', ['validate_schema.py', str(schema_dir)]), \
             patch('os.path.isfile', return_value=False), \
             patch('os.path.isdir', return_value=True), \
             patch('validate_schema.validate_schema_directory', return_value={}), \
             patch('validate_schema.generate_validation_report'):
            exit_code = validate_schema.main()
            assert exit_code == 1 