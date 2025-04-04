# OME XSD to LinkML Schema Converter

## Project Overview
This project provides tools to convert the Open Microscopy Environment (OME) XML Schema Definition (XSD) into LinkML YAML schemas. LinkML (Linked Data Modeling Language) provides a flexible and semantically rich format for representing and validating biological metadata.

The converter extracts elements, attributes, types, and relationships from the OME XSD and transforms them into a structured LinkML schema, preserving documentation and type information.

## Key Features
- **XSD to JSON Schema Conversion**: Converts XML Schema elements to JSON Schema
- **JSON Schema to LinkML Transformation**: Transforms JSON Schema to LinkML YAML format
- **Attribute and Documentation Preservation**: Captures all attributes, descriptions and relationships
- **Schema Partitioning**: Can generate individual schemas for specific OME elements
- **Comprehensive Type Mapping**: Maps XSD types to appropriate LinkML types

## Getting Started

### Prerequisites
- Python 3.8+
- Required Python libraries (install with `pip install -r requirements.txt`):
  - xmlschema
  - pyyaml
  - linkml-runtime
  - requests

### Project Structure
```
📂 project_root
├── 📂 data                 # Contains the OME XSD files
│   └── ome.xsd             # Main OME XSD schema
├── 📂 ome_schemas          # Generated LinkML schemas
│   ├── Pixels.yaml         # Schema for Pixels element
│   ├── Image.yaml          # Schema for Image element
│   └── ...                 # Other element schemas
├── 📂 src                  # Source code
│   ├── download_xsd.py     # Script to download OME XSD file
│   ├── generator.py        # LinkML schema generator
│   ├── validate_schema.py  # Schema validation script
│   └── xsdtojson.py        # XSD to JSON Schema converter
├── 📂 tests                # Test files
│   └── ...                 # Various test modules
├── download_xsd.sh         # Shell script for downloading XSD
├── generate_element_schema.sh # Shell script for generating element schemas
├── generate_full_schema.sh # Shell script for generating complete schema
├── generate_and_validate.sh # Pipeline for generation and validation
├── validation_report.md    # Generated validation report
├── README.md               # This documentation
└── requirements.txt        # Python dependencies
```

## Usage

### Downloading the OME XSD
To download the latest OME XSD file:

```bash
python -m src.download_xsd
```

This will save the file to `data/ome.xsd`.

You can also use the provided shell script:

```bash
./download_xsd.sh
```

### Generating a LinkML Schema

#### Using Python Directly

To generate a full LinkML schema from the OME XSD:

```bash
python -m src.generator data/ome.xsd --output ome_schema.yaml -v
```

To generate partitioned schemas (one file per major element):

```bash
python -m src.generator data/ome.xsd --output schemas_directory --partition -v
```

To generate a schema for a specific element:

```bash
python -m src.generator data/ome.xsd --output specific_element.yaml --elements Image,Pixels -v
```

#### Using Shell Scripts

For convenience, you can use the provided shell scripts:

1. **Generate a complete schema**:
   ```bash
   ./generate_full_schema.sh
   ```
   
   Options:
   - `-o, --output PATH`: Specify output file (default: ome_schema.yaml)
   - `-p, --partition`: Partition schema into separate files
   - `-v, --verbose`: Enable verbose output
   - `-x, --xsd PATH`: Specify XSD file path (default: data/ome.xsd)

2. **Generate schemas for specific elements**:
   ```bash
   ./generate_element_schema.sh --elements Image,Pixels
   ```
   
   Options:
   - `-e, --elements LIST`: Comma-separated list of elements (required)
   - `-o, --output PATH`: Specify output file (default: element_schemas)
   - `-v, --verbose`: Enable verbose output
   - `-x, --xsd PATH`: Specify XSD file path (default: data/ome.xsd)

For help on any script, use the `-h` or `--help` option:
```bash
./generate_full_schema.sh --help
```

### Schema Validation

The project now includes a robust schema validation pipeline that checks the generated LinkML schemas for correctness and consistency. The validation process performs:

1. **YAML Syntax Checking**: Validates the basic structure and syntax of YAML files.
2. **LinkML Compliance**: Ensures adherence to LinkML schema standards (when LinkML is available).
3. **Reference Validation**: Verifies that all references between classes and slots are valid.
4. **Type Checking**: Confirms that all types are properly defined.
5. **Inheritance Validation**: Validates inheritance relationships between classes.

### Validation Features

- **Graceful Degradation**: Falls back to basic YAML validation when LinkML is not available
- **Comprehensive Reporting**: Generates detailed Markdown reports of validation results
- **Flexible Usage**: Can validate individual schemas or entire directories
- **Command-line Interface**: Simple usage through the CLI or the provided shell script

### Limitations

- **Full Validation Requires LinkML**: Some validation checks only work when LinkML is installed
- **Performance**: Validating large schema collections may be time-consuming
- **Basic Mode**: When LinkML is unavailable, only basic YAML syntax is checked

### Usage

The validation can be run as part of the full pipeline:

```bash
./generate_and_validate.sh
```

Or directly on schemas or directories:

```bash
python -m src.validate_schema path/to/schema.yaml --output report.md
python -m src.validate_schema path/to/schema_directory --output report.md
```

Skip validation in the pipeline with:

```bash
./generate_and_validate.sh --no-validate
```

### Windows Compatibility

If you're using Windows, you can run the shell scripts using:

1. **Git Bash**: If you have Git installed, use Git Bash to run the scripts
2. **WSL**: Use Windows Subsystem for Linux
3. **PowerShell**: Convert the scripts to PowerShell format or run them with:
   ```powershell
   bash ./generate_full_schema.sh
   ```
4. **Command Prompt**: If you have bash installed, run:
   ```cmd
   bash generate_full_schema.sh
   ```

Alternatively, you can always use the Python commands directly.

## Implementation Details

The conversion process works in three main stages:

1. **XSD Parsing**: The OME XSD is parsed using the xmlschema library
2. **JSON Schema Conversion**: XSD elements are converted to a JSON Schema representation
3. **LinkML Generation**: The JSON Schema is transformed into LinkML YAML format
4. **Schema Validation**: Generated LinkML schemas are validated for correctness and consistency

The code handles complex features like:
- Element inheritance and extension
- Complex type definitions
- Documentation extraction
- Attribute type mapping
- Enumeration values

## Testing

The project includes a comprehensive test suite. To run the tests:

```bash
python -m pytest
```

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- [Open Microscopy Environment (OME)](https://www.openmicroscopy.org/) for the OME schema
- [LinkML](https://github.com/linkml/linkml) for the schema modeling language

