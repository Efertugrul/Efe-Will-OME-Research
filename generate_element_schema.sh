#!/bin/bash

# Script to generate LinkML schemas for specific OME elements

# Default values
XSD_PATH="data/ome.xsd"
OUTPUT_PATH="element_schemas"
ELEMENTS=""
VERBOSE=false

# Function to display usage
function show_usage {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -x, --xsd PATH             Path to OME XSD file (default: $XSD_PATH)"
    echo "  -o, --output PATH          Output path for generated schema(s) (default: $OUTPUT_PATH)"
    echo "  -e, --elements LIST        Comma-separated list of elements to include (required)"
    echo "  -v, --verbose              Enable verbose output"
    echo
    echo "Example:"
    echo "  $0 --elements Image,Pixels --output image_pixel_schema.yaml"
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
        -e|--elements)
            ELEMENTS="$2"
            shift
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

# Check if elements are specified
if [ -z "$ELEMENTS" ]; then
    echo "Error: You must specify elements using --elements"
    show_usage
fi

# Check if XSD file exists
if [ ! -f "$XSD_PATH" ]; then
    echo "Error: XSD file not found at $XSD_PATH"
    echo "You may need to download it first with: python -m src.download_xsd"
    exit 1
fi

# Build command
CMD="python -m src.generator $XSD_PATH --output $OUTPUT_PATH --elements $ELEMENTS"

# Add verbose flag if enabled
if [ "$VERBOSE" = true ]; then
    CMD="$CMD -v"
fi

# Execute command
echo "Generating LinkML schema for elements: $ELEMENTS"
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