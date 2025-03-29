#!/bin/bash

# Script to download the OME XSD file

# Default values
OUTPUT_DIR="data"
VERBOSE=false

# Function to display usage
function show_usage {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -o, --output DIR           Output directory for the XSD file (default: $OUTPUT_DIR)"
    echo "  -v, --verbose              Enable verbose output"
    echo
    echo "Example:"
    echo "  $0 --output custom_data_dir"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            show_usage
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
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

# Make sure the output directory exists
mkdir -p "$OUTPUT_DIR"

# Build command
CMD="python -m src.download_xsd --output $OUTPUT_DIR/ome.xsd"

# Add verbose flag if enabled
if [ "$VERBOSE" = true ]; then
    CMD="$CMD --verbose"
fi

# Execute command
echo "Downloading OME XSD file"
echo "Command: $CMD"
echo
eval $CMD

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo
    echo "Download completed successfully"
    echo "XSD file saved to: $OUTPUT_DIR/ome.xsd"
else
    echo
    echo "Error: Download failed"
    exit 1
fi 