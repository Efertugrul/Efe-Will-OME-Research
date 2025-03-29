import requests
import os
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OME_XSD_URL = "https://www.openmicroscopy.org/Schemas/OME/2016-06/ome.xsd"

def download_xsd(url, output_path, verbose=False):
    """
    Download the OME XSD file from the specified URL.
    
    Args:
        url (str): URL of the XSD file
        output_path (str): Path to save the downloaded file
        verbose (bool): Whether to output verbose logs
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug(f"Downloading XSD from {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        # Save the XSD file
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        if verbose:
            logger.debug(f"XSD file saved to {output_path}")
        logger.info(f"Successfully downloaded OME XSD to {output_path}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading XSD: {str(e)}")
        raise

def get_ome_xsd_url(version=None):
    """
    Get the URL for the OME XSD file.
    
    Args:
        version (str, optional): Version of the OME XSD (default is latest)
        
    Returns:
        str: URL of the OME XSD file
    """
    if version:
        return f"https://www.openmicroscopy.org/Schemas/OME/{version}/ome.xsd"
    return OME_XSD_URL

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download OME XSD file")
    parser.add_argument("--output", help="Output path for the XSD file", default="data/ome.xsd")
    parser.add_argument("--url", help="URL of the XSD file", default=OME_XSD_URL)
    parser.add_argument("--version", help="OME XSD version (e.g., '2016-06')")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # If version is specified, use it to generate the URL
    url = args.url
    if args.version:
        url = get_ome_xsd_url(args.version)
    
    download_xsd(url, args.output, args.verbose) 