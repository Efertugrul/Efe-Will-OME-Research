#!/bin/bash

# Script to generate LinkML schemas and then validate them in a pipeline

# Default values
XSD_PATH="data/ome.xsd"
OUTPUT_DIR="ome_schemas"
VALIDATION_REPORT="validation_report.md"
VERBOSE=false
PARTITION=true

# Function to display usage
function show_usage {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -x, --xsd PATH             Path to OME XSD file (default: $XSD_PATH)"
    echo "  -o, --output DIR           Output directory for generated schemas (default: $OUTPUT_DIR)"
    echo "  -r, --report FILE          Path to save validation report (default: $VALIDATION_REPORT)"
    echo "  -s, --single               Generate a single schema file instead of partitioning"
    echo "  -v, --verbose              Enable verbose output"
    echo
    echo "Examples:"
    echo "  $0                          # Generate and validate schemas with default settings"
    echo "  $0 --single --output ome_schema.yaml  # Generate a single schema and validate it"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            show_usage
            ;;
        -x|--xsd)
            XSD_PATH="$2"
            shift
            shift
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift
            shift
            ;;
        -r|--report)
            VALIDATION_REPORT="$2"
            shift
            shift
            ;;
        -s|--single)
            PARTITION=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Check if XSD file exists
if [ ! -f "$XSD_PATH" ]; then
    echo "Error: XSD file not found at $XSD_PATH"
    echo "You may need to download it first with: python -m src.download_xsd"
    exit 1
fi

# Step 1: Generate LinkML schemas
echo "Step 1: Generating LinkML schemas..."

# Build generation command
if [ "$PARTITION" = true ]; then
    GEN_CMD="python -m src.generator $XSD_PATH --output $OUTPUT_DIR --partition"
    echo "Generating partitioned schemas in $OUTPUT_DIR"
else
    GEN_CMD="python -m src.generator $XSD_PATH --output $OUTPUT_DIR"
    echo "Generating single schema file $OUTPUT_DIR"
fi

# Add verbose flag if enabled
if [ "$VERBOSE" = true ]; then
    GEN_CMD="$GEN_CMD -v"
fi

# Execute generation command
echo "Command: $GEN_CMD"
echo
eval $GEN_CMD

# Check if generation was successful
if [ $? -ne 0 ]; then
    echo
    echo "Error: Schema generation failed"
    exit 1
fi

echo
echo "Schema generation completed successfully"
echo

# Step 2: Validate the generated schemas
echo "Step 2: Validating generated schemas..."

# Build validation command
VALIDATE_CMD="python -m src.validate_schema $OUTPUT_DIR --output $VALIDATION_REPORT"

# Add verbose flag if enabled
if [ "$VERBOSE" = true ]; then
    VALIDATE_CMD="$VALIDATE_CMD -v"
fi

# Execute validation command
echo "Command: $VALIDATE_CMD"
echo
eval $VALIDATE_CMD

# Check if validation was successful
VALIDATION_RESULT=$?
if [ $VALIDATION_RESULT -eq 0 ]; then
    echo
    echo "Schema validation completed successfully"
    echo "All schemas are valid"
    echo
    echo "Pipeline completed successfully!"
else
    echo
    echo "Schema validation completed with errors"
    echo "See validation report at $VALIDATION_REPORT for details"
    echo
    echo "Pipeline completed with validation errors"
    exit $VALIDATION_RESULT
fi 