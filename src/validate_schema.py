#!/usr/bin/env python
"""
Schema Validation Script for LinkML Schemas

This script provides functionality to validate LinkML YAML schemas
using the LinkML validator tools. It checks for syntax errors, 
reference consistency, and semantic correctness.
"""

import os
import sys
import logging
import argparse
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

# Import LinkML validation tools
try:
    # Try standard import path first
    from linkml_runtime.loaders import yaml_loader
    from linkml_runtime.utils.schemaview import SchemaView
    from linkml_runtime.utils.validate_yaml import validate_yaml
    try:
        from linkml.validators.jsonschemavalidator import JsonSchemaValidator
    except ImportError:
        # Some installations use different module names
        from linkml_runtime.validators.jsonschemavalidator import JsonSchemaValidator
except ImportError:
    print("Error: LinkML packages not found. Please install them with:")
    print("pip install linkml linkml-runtime")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_schema_file(schema_file: str, verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate a single LinkML schema file.
    
    Args:
        schema_file: Path to the schema file
        verbose: Whether to output detailed validation information
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
        
    errors = []
    
    try:
        # Check if file exists
        if not os.path.exists(schema_file):
            errors.append(f"File not found: {schema_file}")
            return False, errors
            
        # Check YAML syntax
        logger.debug(f"Checking YAML syntax for {schema_file}")
        try:
            with open(schema_file, 'r') as f:
                yaml_content = yaml.safe_load(f)
                
            if yaml_content is None:
                errors.append(f"Invalid or empty YAML: {schema_file}")
                return False, errors
        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error in {schema_file}: {str(e)}")
            return False, errors
            
        # Load schema with LinkML
        logger.debug(f"Loading schema with LinkML: {schema_file}")
        try:
            schema = yaml_loader.load(schema_file, target_class=dict)
            view = SchemaView(schema)
        except Exception as e:
            errors.append(f"LinkML schema loading error in {schema_file}: {str(e)}")
            return False, errors
            
        # Validate schema structure
        logger.debug(f"Validating schema structure: {schema_file}")
        if 'id' not in schema:
            errors.append(f"Missing 'id' field in schema: {schema_file}")
        if 'name' not in schema:
            errors.append(f"Missing 'name' field in schema: {schema_file}")
            
        # Validate classes and slots
        if 'classes' in schema:
            for class_name, class_def in schema['classes'].items():
                logger.debug(f"Validating class: {class_name}")
                # Check for required class properties
                if not isinstance(class_def, dict):
                    errors.append(f"Class definition for {class_name} is not a dictionary")
                    continue
                
                # Check class references
                if 'is_a' in class_def:
                    parent_class = class_def['is_a']
                    if parent_class not in schema['classes']:
                        errors.append(f"Class {class_name} references undefined parent class {parent_class}")
                
                # Check slot references
                if 'slots' in class_def:
                    if not isinstance(class_def['slots'], list):
                        errors.append(f"Slots in class {class_name} should be a list")
                    else:
                        for slot_name in class_def['slots']:
                            if 'slots' not in schema or slot_name not in schema['slots']:
                                errors.append(f"Class {class_name} references undefined slot {slot_name}")
        
        # Validate slots
        if 'slots' in schema:
            for slot_name, slot_def in schema['slots'].items():
                logger.debug(f"Validating slot: {slot_name}")
                # Check for required slot properties
                if not isinstance(slot_def, dict):
                    errors.append(f"Slot definition for {slot_name} is not a dictionary")
                    continue
                
                # Check range references
                if 'range' in slot_def:
                    range_type = slot_def['range']
                    if range_type not in ['string', 'integer', 'boolean', 'float', 'date', 'datetime'] and \
                       ('classes' not in schema or range_type not in schema['classes']) and \
                       ('types' not in schema or range_type not in schema['types']):
                        errors.append(f"Slot {slot_name} references undefined range {range_type}")
        
        # Run LinkML validators if available
        try:
            validator = JsonSchemaValidator(schema_file)
            validation_results = validator.validate()
            if not validation_results.valid:
                for error in validation_results.results:
                    errors.append(f"LinkML validation error: {error}")
        except Exception as e:
            logger.debug(f"Could not use JsonSchemaValidator: {str(e)}")
            # Fall back to basic validation
            pass
        
        if errors:
            return False, errors
        else:
            return True, []
            
    except Exception as e:
        errors.append(f"Unexpected error validating {schema_file}: {str(e)}")
        return False, errors

def validate_schema_directory(directory: str, verbose: bool = False) -> Dict[str, Tuple[bool, List[str]]]:
    """
    Validate all LinkML schema files in a directory.
    
    Args:
        directory: Path to directory containing schema files
        verbose: Whether to output detailed validation information
    
    Returns:
        Dictionary mapping filenames to (is_valid, error_messages) tuples
    """
    if not os.path.isdir(directory):
        logger.error(f"Directory not found: {directory}")
        return {}
        
    results = {}
    
    # Find all YAML files
    yaml_files = list(Path(directory).glob('*.yaml')) + list(Path(directory).glob('*.yml'))
    
    if not yaml_files:
        logger.warning(f"No YAML files found in {directory}")
        return {}
        
    # Validate each file
    for yaml_file in yaml_files:
        file_path = str(yaml_file)
        logger.info(f"Validating {file_path}")
        is_valid, errors = validate_schema_file(file_path, verbose)
        results[file_path] = (is_valid, errors)
        
        # Print results immediately
        if is_valid:
            logger.info(f"✓ {file_path} is valid")
        else:
            logger.error(f"✗ {file_path} has {len(errors)} errors:")
            for error in errors:
                logger.error(f"  - {error}")
    
    return results

def generate_validation_report(results: Dict[str, Tuple[bool, List[str]]], output_file: Optional[str] = None):
    """
    Generate a validation report from validation results.
    
    Args:
        results: Dictionary mapping filenames to (is_valid, error_messages) tuples
        output_file: Path to output file for report
    """
    valid_count = sum(1 for is_valid, _ in results.values() if is_valid)
    total_count = len(results)
    
    report = []
    report.append("# LinkML Schema Validation Report")
    report.append("")
    report.append(f"## Summary")
    report.append("")
    report.append(f"- Total schemas validated: {total_count}")
    report.append(f"- Valid schemas: {valid_count}")
    report.append(f"- Invalid schemas: {total_count - valid_count}")
    report.append("")
    
    if total_count - valid_count > 0:
        report.append("## Details of Invalid Schemas")
        report.append("")
        
        for file_path, (is_valid, errors) in results.items():
            if not is_valid:
                report.append(f"### {os.path.basename(file_path)}")
                report.append("")
                report.append(f"File: `{file_path}`")
                report.append("")
                report.append("Errors:")
                report.append("")
                for error in errors:
                    report.append(f"- {error}")
                report.append("")
    
    report_text = "\n".join(report)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report_text)
        logger.info(f"Validation report saved to {output_file}")
    else:
        print("\n" + report_text)
    
    return report_text

def main():
    """Main function to run validation from command line"""
    parser = argparse.ArgumentParser(description="Validate LinkML schemas")
    
    # Add arguments
    parser.add_argument("path", help="Path to a LinkML schema file or directory of schema files")
    parser.add_argument("--output", "-o", help="Path to save validation report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if path is a file or directory
    if os.path.isfile(args.path):
        # Validate single file
        is_valid, errors = validate_schema_file(args.path, args.verbose)
        results = {args.path: (is_valid, errors)}
        
        # Print results
        if is_valid:
            logger.info(f"✓ {args.path} is valid")
            if args.output:
                generate_validation_report(results, args.output)
            return 0
        else:
            logger.error(f"✗ {args.path} has {len(errors)} errors:")
            for error in errors:
                logger.error(f"  - {error}")
            if args.output:
                generate_validation_report(results, args.output)
            return 1
    
    elif os.path.isdir(args.path):
        # Validate directory
        results = validate_schema_directory(args.path, args.verbose)
        
        # Generate report
        if args.output:
            generate_validation_report(results, args.output)
        
        # Return appropriate exit code
        if all(is_valid for is_valid, _ in results.values()):
            return 0
        else:
            return 1
    
    else:
        logger.error(f"Path not found: {args.path}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 