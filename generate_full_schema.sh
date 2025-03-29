#!/bin/bash

# Script to generate a complete LinkML schema from the OME XSD

# Default values
XSD_PATH="data/ome.xsd"
OUTPUT_PATH="ome_schema.yaml"
PARTITION=false
VERBOSE=false

# Function to display usage
function show_usage {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -x, --xsd PATH             Path to OME XSD file (default: $XSD_PATH)"
    echo "  -o, --output PATH          Output path for generated schema(s) (default: $OUTPUT_PATH)"
    echo "  -p, --partition            Partition the schema into separate files by element"
    echo "  -v, --verbose              Enable verbose output"
    echo
    echo "Examples:"
    echo "  $0                          # Generate complete schema in ome_schema.yaml"
    echo "  $0 --partition --output ome_schemas  # Generate partitioned schemas in ome_schemas directory"
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
            OUTPUT_PATH="$2"
            shift
            shift
            ;;
        -p|--partition)
            PARTITION=true
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

# Build command
CMD="python -m src.generator $XSD_PATH --output $OUTPUT_PATH"

# Add partition flag if enabled
if [ "$PARTITION" = true ]; then
    CMD="$CMD --partition"
    echo "Generating partitioned LinkML schema"
else
    echo "Generating complete LinkML schema"
fi

# Add verbose flag if enabled
if [ "$VERBOSE" = true ]; then
    CMD="$CMD -v"
fi

# Execute command
echo "Command: $CMD"
echo
eval $CMD

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo
    echo "Schema generation completed successfully"
    echo "Output saved to: $OUTPUT_PATH"
else
    echo
    echo "Error: Schema generation failed"
    exit 1
fi 