import argparse
import os
import xmlschema
from typing import Dict, List, Optional, Union
import yaml
from pathlib import Path
import json
import logging
from collections import defaultdict

# Fix import for both module and direct script usage
try:
    from src.xsdtojson import xsd_to_json_schema
except ImportError:
    from xsdtojson import xsd_to_json_schema
from linkml_runtime.utils.schemaview import SchemaView
from linkml_runtime.dumpers import yaml_dumper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_linkml_schema(ome_xsd_path, output_path=None, top_level_elements=None, partition=False):
    """
    Generate a LinkML schema from an OME XSD file.
    
    Args:
        ome_xsd_path: Path to the OME XSD file
        output_path: Path to output the LinkML schema
        top_level_elements: List of top-level elements to include (if None, include all)
        partition: Whether to partition the schema into separate files
    
    Returns:
        A dictionary containing the LinkML schema
    """
    try:
        # Parse the XSD using xmlschema
        xsd = xmlschema.XMLSchema(ome_xsd_path)
        
        # Convert to JSON Schema
        json_schema = xsd_to_json_schema(ome_xsd_path)
        
        # Filter top-level elements if specified
        if top_level_elements:
            filtered_props = {}
            filtered_defs = {}
            
            # Keep only specified top-level elements
            for element in top_level_elements:
                if element in json_schema.get("properties", {}):
                    filtered_props[element] = json_schema["properties"][element]
                
                # Include associated definitions
                if "definitions" in json_schema:
                    for def_name, def_value in json_schema["definitions"].items():
                        if def_name.startswith(element) or def_name in [ref.split("/")[-1] for ref in filtered_props.get(element, {}).get("$ref", "").split()]:
                            filtered_defs[def_name] = def_value
            
            # Update JSON schema with filtered values
            json_schema["properties"] = filtered_props
            if filtered_defs:
                json_schema["definitions"] = filtered_defs
        
        # Convert JSON Schema to LinkML
        linkml_schema = convert_json_schema_to_linkml(json_schema, xsd)
        
        # Output schema
        if output_path:
            if partition and "classes" in linkml_schema:
                # Create directory if it doesn't exist
                if not os.path.exists(output_path):
                    os.makedirs(output_path)
                
                # Partition schema by top-level classes
                for class_name, class_def in list(linkml_schema["classes"].items()):
                    if class_name.endswith("Ref") or class_name in ["Map", "ManufacturerSpec", "LightSource", "Reference", "FilterRef", "Settings", "Annotation", "BasicAnnotation", "NumericAnnotation", "TextAnnotation", "TypeAnnotation", "Shape", "AffineTransform"]:
                        continue
                    
                    # Create a new schema with just this class
                    partitioned_schema = {
                        "id": linkml_schema["id"],
                        "name": linkml_schema["name"],
                        "title": linkml_schema["title"],
                        "description": linkml_schema["description"],
                        "license": linkml_schema["license"],
                        "version": linkml_schema["version"],
                        "prefixes": linkml_schema["prefixes"],
                        "default_prefix": linkml_schema["default_prefix"],
                        "types": linkml_schema["types"],
                        "classes": {
                            class_name: class_def,
                            # Include common types
                            "ManufacturerSpec": linkml_schema["classes"]["ManufacturerSpec"],
                            "Map": linkml_schema["classes"]["Map"],
                            "LightSource": linkml_schema["classes"]["LightSource"],
                            "Reference": linkml_schema["classes"]["Reference"],
                            "FilterRef": linkml_schema["classes"]["FilterRef"],
                            "Settings": linkml_schema["classes"]["Settings"],
                            "Annotation": linkml_schema["classes"]["Annotation"],
                            "BasicAnnotation": linkml_schema["classes"]["BasicAnnotation"],
                            "NumericAnnotation": linkml_schema["classes"]["NumericAnnotation"],
                            "TextAnnotation": linkml_schema["classes"]["TextAnnotation"],
                            "TypeAnnotation": linkml_schema["classes"]["TypeAnnotation"],
                            "Shape": linkml_schema["classes"]["Shape"],
                            "AffineTransform": linkml_schema["classes"]["AffineTransform"]
                        },
                        "slots": {}
                    }
                    
                    # Add relevant slots
                    for slot_name, slot_def in linkml_schema["slots"].items():
                        if slot_name.startswith(f"attr_") and class_name in slot_def.get("description", ""):
                            partitioned_schema["slots"][slot_name] = slot_def
                    
                    # Add common slots
                    for slot_name, slot_def in linkml_schema["slots"].items():
                        if "ManufacturerSpec" in slot_def.get("description", "") or \
                           "LightSource" in slot_def.get("description", "") or \
                           "Annotation" in slot_def.get("description", "") or \
                           "Shape" in slot_def.get("description", "") or \
                           "AffineTransform" in slot_def.get("description", ""):
                            partitioned_schema["slots"][slot_name] = slot_def
                    
                    # Write to file
                    class_file_path = os.path.join(output_path, f"{class_name}.yaml")
                    with open(class_file_path, 'w') as f:
                        yaml.dump(partitioned_schema, f, sort_keys=False)
                
                logger.info(f"Successfully partitioned schema into {len(linkml_schema['classes'])} files in {output_path}")
            else:
                # Write full schema to a single file
                # Ensure the output path has a .yaml extension
                if not output_path.endswith('.yaml') and not output_path.endswith('.yml'):
                    output_path = f"{output_path}.yaml"
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
                
                # Use yaml_dumper for consistent YAML format
                with open(output_path, 'w') as f:
                    yaml.dump(linkml_schema, f, sort_keys=False, default_flow_style=False)
                
                logger.info(f"Successfully generated LinkML schema at {output_path}")
        
        return linkml_schema
    
    except Exception as e:
        logger.error(f"Error generating LinkML schema: {str(e)}")
        raise

def convert_json_schema_to_linkml(json_schema, xsd):
    """
    Convert a JSON Schema to a LinkML schema.
    
    Args:
        json_schema: JSON Schema dictionary
        xsd: The original XMLSchema object for documentation and inheritance information
    
    Returns:
        A dictionary containing the LinkML schema
    """
    # Create basic LinkML schema structure
    linkml_schema = {
        "id": "https://w3id.org/linkml/ome",
        "name": "ome",
        "title": "OME Schema",
        "description": "LinkML translation of the OME XML Schema",
        "license": "https://creativecommons.org/publicdomain/zero/1.0/",
        "version": "0.0.1",
        "prefixes": {
            "linkml": "https://w3id.org/linkml/",
            "ome": "https://www.openmicroscopy.org/Schemas/OME/",
            "schema": "http://schema.org/",
            "xsd": "http://www.w3.org/2001/XMLSchema#"
        },
        "default_prefix": "ome",
        "types": {
            "string": {
                "uri": "xsd:string",
                "description": "A character string"
            },
            "integer": {
                "uri": "xsd:integer",
                "description": "An integer"
            },
            "boolean": {
                "uri": "xsd:boolean",
                "description": "A binary (true or false) value"
            },
            "float": {
                "uri": "xsd:float",
                "description": "A floating point number"
            },
            "date": {
                "uri": "xsd:date",
                "description": "A date"
            },
            "datetime": {
                "uri": "xsd:dateTime",
                "description": "A date and time"
            }
        },
        "classes": {},
        "slots": {}
    }
    
    # Get complex type hierarchy from XSD
    complex_types = {}
    inheritance_map = {}
    
    # Extract complex types and their inheritance
    for type_name, type_def in xsd.types.items():
        if type_def.is_complex() and not type_name.startswith('{'):
            complex_types[type_name] = type_def
            # Check for base types (inheritance)
            if hasattr(type_def, 'content') and hasattr(type_def.content, 'base_type'):
                base_type = type_def.content.base_type
                if base_type and hasattr(base_type, 'name') and base_type.name:
                    base_name = base_type.name.split("}")[-1]  # Remove namespace
                    inheritance_map[type_name] = base_name
    
    # Create a class for each complex type
    for type_name, type_def in complex_types.items():
        if type_name in linkml_schema["classes"]:
            continue
            
        linkml_schema["classes"][type_name] = {
            "description": f"Complex type {type_name}",
            "slots": [],
            "attributes": {}
        }
        
        # Get documentation if available
        if hasattr(type_def, 'annotation') and type_def.annotation:
            doc = _get_documentation(type_def.annotation)
            if doc:
                linkml_schema["classes"][type_name]["description"] = _ensure_serializable(doc)
        
        # Add inheritance (is_a)
        if type_name in inheritance_map:
            base_type = inheritance_map[type_name]
            if base_type in linkml_schema["classes"]:
                linkml_schema["classes"][type_name]["is_a"] = base_type
        
    # Process elements to create classes and slots
    for elem_name, elem_def in xsd.elements.items():
        element_name = elem_name.split("}")[-1]  # Remove namespace
        
        if element_name in linkml_schema["classes"]:
            continue
            
        # Create class for element
        linkml_schema["classes"][element_name] = {
            "description": f"The {element_name} element from the XML Schema.",
            "slots": [],
            "attributes": {}
        }
        
        # Get documentation if available
        if hasattr(elem_def, 'annotation') and elem_def.annotation:
            doc = _get_documentation(elem_def.annotation)
            if doc:
                linkml_schema["classes"][element_name]["description"] = _ensure_serializable(doc)
        
        # Check if this element extends a complex type
        if hasattr(elem_def, 'type') and hasattr(elem_def.type, 'content'):
            type_content = elem_def.type.content
            if hasattr(type_content, 'base_type') and type_content.base_type:
                base_type = type_content.base_type
                if hasattr(base_type, 'name'):
                    base_name = base_type.name.split("}")[-1]
                    if base_name in linkml_schema["classes"]:
                        linkml_schema["classes"][element_name]["is_a"] = base_name
                        
                        # Inherit slots from base class
                        base_slots = linkml_schema["classes"][base_name].get("slots", [])
                        linkml_schema["classes"][element_name]["slots"].extend(base_slots)
                        
                        # Inherit attributes from base class
                        base_attrs = linkml_schema["classes"][base_name].get("attributes", {})
                        for attr_name, attr_slot in base_attrs.items():
                            linkml_schema["classes"][element_name]["attributes"][attr_name] = attr_slot
        
    # Add properties and attributes from JSON schema
    for prop_name, prop_def in json_schema.get("properties", {}).items():
        if prop_name not in linkml_schema["classes"]:
            continue
            
        # Process attributes in the property
        if "properties" in prop_def:
            for attr_name, attr_def in prop_def["properties"].items():
                # Skip attributes that start with @ (these are XML attributes)
                if attr_name.startswith('@'):
                    attr_name = attr_name[1:]  # Remove @ prefix
                
                slot_name = f"attr_{attr_name.lower()}"
                
                # Check if slot already exists
                if slot_name not in linkml_schema["slots"]:
                    linkml_schema["slots"][slot_name] = {
                        "description": f"Attribute {attr_name} of {prop_name}",
                        "range": _map_json_type_to_linkml_type(attr_def.get("type", "string"))
                    }
                    
                    # Add documentation if available
                    if "description" in attr_def:
                        linkml_schema["slots"][slot_name]["description"] = _ensure_serializable(attr_def["description"])
                    
                    # Add enumerations if available
                    if "enum" in attr_def:
                        linkml_schema["slots"][slot_name]["enum_values"] = {
                            enum_val: {"description": f"{enum_val} value"} 
                            for enum_val in attr_def["enum"]
                        }
                    
                    # Add required flag
                    if "required" in prop_def and attr_name in prop_def["required"]:
                        linkml_schema["slots"][slot_name]["required"] = True
                
                # Add slot to class and track in attributes mapping
                if slot_name not in linkml_schema["classes"][prop_name]["slots"]:
                    linkml_schema["classes"][prop_name]["slots"].append(slot_name)
                linkml_schema["classes"][prop_name]["attributes"][attr_name] = slot_name
    
    _add_common_base_classes(linkml_schema)
    
    return _ensure_schema_serializable(linkml_schema)

def _get_documentation(annotation):
    """
    Extract documentation from an XSD annotation.
    
    Args:
        annotation: The XSD annotation object
        
    Returns:
        Documentation string or None
    """
    if not annotation:
        return None
        
    # Try to access documentation via different methods
    try:
        # Method 1: Try directly accessing documentation
        if hasattr(annotation, 'documentation'):
            return annotation.documentation
            
        # Method 2: Try to access annotation documentation via children/elements
        if hasattr(annotation, 'elem') and annotation.elem is not None:
            for child in annotation.elem:
                if child.tag.endswith('documentation'):
                    return child.text.strip() if child.text else ""
                    
        # Method 3: Try accessing via lxml attributes
        if hasattr(annotation, 'elem') and hasattr(annotation.elem, 'findall'):
            doc_elems = annotation.elem.findall('.//{*}documentation')
            if doc_elems and len(doc_elems) > 0:
                return doc_elems[0].text.strip() if doc_elems[0].text else ""
                
        # Method 4: Try direct XML parsing if available in the schema
        if hasattr(annotation, 'schema') and hasattr(annotation.schema, 'xpath'):
            doc_nodes = annotation.schema.xpath('.//xs:documentation', namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'})
            if doc_nodes and len(doc_nodes) > 0:
                return doc_nodes[0].text.strip() if doc_nodes[0].text else ""
                
    except Exception as e:
        logger.debug(f"Error extracting documentation: {str(e)}")
        
    # If all else fails, try to extract from string representation
    try:
        annotation_str = str(annotation)
        if 'documentation' in annotation_str:
            import re
            match = re.search(r'<documentation>(.*?)</documentation>', annotation_str, re.DOTALL)
            if match:
                return match.group(1).strip()
    except Exception:
        pass
        
    return None

def _add_common_base_classes(linkml_schema):
    """Add common base classes required in the schema"""
    
    # Reference class (used by all *Ref elements)
    if "Reference" not in linkml_schema["classes"]:
        linkml_schema["classes"]["Reference"] = {
            "description": "Complex type Reference",
            "slots": [],
            "attributes": {}
        }
    
    # ManufacturerSpec class
    if "ManufacturerSpec" not in linkml_schema["classes"]:
        linkml_schema["classes"]["ManufacturerSpec"] = {
            "description": "Complex type ManufacturerSpec",
            "slots": [
                "attr_manufacturer",
                "attr_model",
                "attr_serialnumber",
                "attr_lotnumber"
            ],
            "attributes": {
                "Manufacturer": "attr_manufacturer",
                "Model": "attr_model",
                "SerialNumber": "attr_serialnumber",
                "LotNumber": "attr_lotnumber"
            }
        }
        
        if "attr_manufacturer" not in linkml_schema["slots"]:
            linkml_schema["slots"]["attr_manufacturer"] = {
                "description": "Attribute Manufacturer of ManufacturerSpec",
                "range": "string"
            }
            
        if "attr_model" not in linkml_schema["slots"]:
            linkml_schema["slots"]["attr_model"] = {
                "description": "Attribute Model of ManufacturerSpec",
                "range": "string"
            }
            
        if "attr_serialnumber" not in linkml_schema["slots"]:
            linkml_schema["slots"]["attr_serialnumber"] = {
                "description": "Attribute SerialNumber of ManufacturerSpec",
                "range": "string"
            }
            
        if "attr_lotnumber" not in linkml_schema["slots"]:
            linkml_schema["slots"]["attr_lotnumber"] = {
                "description": "Attribute LotNumber of ManufacturerSpec",
                "range": "string"
            }
    
    # Map class
    if "Map" not in linkml_schema["classes"]:
        linkml_schema["classes"]["Map"] = {
            "description": "Complex type Map",
            "slots": [],
            "attributes": {}
        }
    
    # LightSource class
    if "LightSource" not in linkml_schema["classes"]:
        linkml_schema["classes"]["LightSource"] = {
            "description": "Complex type LightSource",
            "slots": [
                "attr_manufacturer",
                "attr_model",
                "attr_serialnumber",
                "attr_lotnumber",
                "attr_id",
                "attr_power",
                "attr_powerunit"
            ],
            "attributes": {
                "Manufacturer": "attr_manufacturer",
                "Model": "attr_model",
                "SerialNumber": "attr_serialnumber",
                "LotNumber": "attr_lotnumber",
                "ID": "attr_id",
                "Power": "attr_power",
                "PowerUnit": "attr_powerunit"
            }
        }
        
        if "attr_power" not in linkml_schema["slots"]:
            linkml_schema["slots"]["attr_power"] = {
                "description": "Attribute Power of LightSource",
                "range": "number"
            }
            
        if "attr_powerunit" not in linkml_schema["slots"]:
            linkml_schema["slots"]["attr_powerunit"] = {
                "description": "Attribute PowerUnit of LightSource",
                "range": "object"
            }
    
    # FilterRef class
    if "FilterRef" not in linkml_schema["classes"]:
        linkml_schema["classes"]["FilterRef"] = {
            "description": "Complex type FilterRef",
            "slots": ["attr_id"],
            "attributes": {"ID": "attr_id"}
        }
    
    # Settings class
    if "Settings" not in linkml_schema["classes"]:
        linkml_schema["classes"]["Settings"] = {
            "description": "Complex type Settings",
            "slots": [],
            "attributes": {}
        }
    
    # Annotation class
    if "Annotation" not in linkml_schema["classes"]:
        linkml_schema["classes"]["Annotation"] = {
            "description": "Complex type Annotation",
            "slots": ["attr_id", "attr_namespace", "attr_annotator"],
            "attributes": {
                "ID": "attr_id",
                "Namespace": "attr_namespace",
                "Annotator": "attr_annotator"
            }
        }
        
        if "attr_namespace" not in linkml_schema["slots"]:
            linkml_schema["slots"]["attr_namespace"] = {
                "description": "Attribute Namespace of Annotation",
                "range": "string"
            }
            
        if "attr_annotator" not in linkml_schema["slots"]:
            linkml_schema["slots"]["attr_annotator"] = {
                "description": "Attribute Annotator of Annotation",
                "range": "object"
            }
    
    # BasicAnnotation class
    if "BasicAnnotation" not in linkml_schema["classes"]:
        linkml_schema["classes"]["BasicAnnotation"] = {
            "description": "Complex type BasicAnnotation",
            "slots": ["attr_id", "attr_namespace", "attr_annotator"],
            "attributes": {
                "ID": "attr_id",
                "Namespace": "attr_namespace",
                "Annotator": "attr_annotator"
            }
        }
    
    # NumericAnnotation class
    if "NumericAnnotation" not in linkml_schema["classes"]:
        linkml_schema["classes"]["NumericAnnotation"] = {
            "description": "Complex type NumericAnnotation",
            "slots": ["attr_id", "attr_namespace", "attr_annotator"],
            "attributes": {
                "ID": "attr_id",
                "Namespace": "attr_namespace",
                "Annotator": "attr_annotator"
            }
        }
    
    # TextAnnotation class
    if "TextAnnotation" not in linkml_schema["classes"]:
        linkml_schema["classes"]["TextAnnotation"] = {
            "description": "Complex type TextAnnotation",
            "slots": ["attr_id", "attr_namespace", "attr_annotator"],
            "attributes": {
                "ID": "attr_id",
                "Namespace": "attr_namespace",
                "Annotator": "attr_annotator"
            }
        }
    
    # TypeAnnotation class
    if "TypeAnnotation" not in linkml_schema["classes"]:
        linkml_schema["classes"]["TypeAnnotation"] = {
            "description": "Complex type TypeAnnotation",
            "slots": ["attr_id", "attr_namespace", "attr_annotator"],
            "attributes": {
                "ID": "attr_id",
                "Namespace": "attr_namespace",
                "Annotator": "attr_annotator"
            }
        }
    
    # Shape class
    if "Shape" not in linkml_schema["classes"]:
        linkml_schema["classes"]["Shape"] = {
            "description": "Complex type Shape",
            "slots": [
                "attr_fillcolor", "attr_fillrule", "attr_strokecolor", "attr_strokewidth",
                "attr_strokewidthunit", "attr_strokedasharray", "attr_text", "attr_fontfamily",
                "attr_fontsize", "attr_fontsizeunit", "attr_fontstyle", "attr_locked",
                "attr_id", "attr_thez", "attr_thet", "attr_thec"
            ],
            "attributes": {
                "FillColor": "attr_fillcolor",
                "FillRule": "attr_fillrule",
                "StrokeColor": "attr_strokecolor",
                "StrokeWidth": "attr_strokewidth",
                "StrokeWidthUnit": "attr_strokewidthunit",
                "StrokeDashArray": "attr_strokedasharray",
                "Text": "attr_text",
                "FontFamily": "attr_fontfamily",
                "FontSize": "attr_fontsize",
                "FontSizeUnit": "attr_fontsizeunit",
                "FontStyle": "attr_fontstyle",
                "Locked": "attr_locked",
                "ID": "attr_id",
                "TheZ": "attr_thez",
                "TheT": "attr_thet",
                "TheC": "attr_thec"
            }
        }
        
        # Add Shape slots if they don't exist
        shape_slots = {
            "attr_fillcolor": {"description": "Attribute FillColor of Shape", "range": "object"},
            "attr_fillrule": {"description": "Attribute FillRule of Shape", "range": "string"},
            "attr_strokecolor": {"description": "Attribute StrokeColor of Shape", "range": "object"},
            "attr_strokewidth": {"description": "Attribute StrokeWidth of Shape", "range": "number"},
            "attr_strokewidthunit": {"description": "Attribute StrokeWidthUnit of Shape", "range": "object"},
            "attr_strokedasharray": {"description": "Attribute StrokeDashArray of Shape", "range": "string"},
            "attr_text": {"description": "Attribute Text of Shape", "range": "string"},
            "attr_fontfamily": {"description": "Attribute FontFamily of Shape", "range": "string"},
            "attr_fontsize": {"description": "Attribute FontSize of Shape", "range": "object"},
            "attr_fontsizeunit": {"description": "Attribute FontSizeUnit of Shape", "range": "object"},
            "attr_fontstyle": {"description": "Attribute FontStyle of Shape", "range": "string"},
            "attr_locked": {"description": "Attribute Locked of Shape", "range": "boolean"},
            "attr_thez": {"description": "Attribute TheZ of Shape", "range": "object"},
            "attr_thet": {"description": "Attribute TheT of Shape", "range": "object"},
            "attr_thec": {"description": "Attribute TheC of Shape", "range": "object"}
        }
        
        for slot_name, slot_def in shape_slots.items():
            if slot_name not in linkml_schema["slots"]:
                linkml_schema["slots"][slot_name] = slot_def
    
    # AffineTransform class
    if "AffineTransform" not in linkml_schema["classes"]:
        linkml_schema["classes"]["AffineTransform"] = {
            "description": "Complex type AffineTransform",
            "slots": ["attr_a00", "attr_a10", "attr_a01", "attr_a11", "attr_a02", "attr_a12"],
            "attributes": {
                "A00": "attr_a00",
                "A10": "attr_a10",
                "A01": "attr_a01",
                "A11": "attr_a11",
                "A02": "attr_a02",
                "A12": "attr_a12"
            }
        }
        
        # Add AffineTransform slots if they don't exist
        affine_slots = {
            "attr_a00": {"description": "Attribute A00 of AffineTransform", "range": "number", "required": True},
            "attr_a10": {"description": "Attribute A10 of AffineTransform", "range": "number", "required": True},
            "attr_a01": {"description": "Attribute A01 of AffineTransform", "range": "number", "required": True},
            "attr_a11": {"description": "Attribute A11 of AffineTransform", "range": "number", "required": True},
            "attr_a02": {"description": "Attribute A02 of AffineTransform", "range": "number", "required": True},
            "attr_a12": {"description": "Attribute A12 of AffineTransform", "range": "number", "required": True}
        }
        
        for slot_name, slot_def in affine_slots.items():
            if slot_name not in linkml_schema["slots"]:
                linkml_schema["slots"][slot_name] = slot_def

def _map_json_type_to_linkml_type(json_type):
    """Map JSON Schema types to LinkML types"""
    type_map = {
        "string": "string",
        "integer": "integer",
        "number": "float",
        "boolean": "boolean",
        "object": "object",
        "array": "array"
    }
    return type_map.get(json_type, "object")

def _ensure_serializable(value):
    """
    Ensure a value is serializable to YAML.
    
    Args:
        value: The value to check
        
    Returns:
        A YAML-serializable version of the value
    """
    # Handle Element objects from the lxml or xml.etree modules
    if hasattr(value, 'tag') and hasattr(value, 'text'):
        return value.text.strip() if value.text else ""
    
    # Return other primitives as is
    return str(value) if not isinstance(value, (str, int, float, bool, list, dict, type(None))) else value

def _ensure_schema_serializable(schema):
    """
    Ensure all values in the schema are serializable to YAML.
    
    Args:
        schema: The schema to check
        
    Returns:
        A YAML-serializable version of the schema
    """
    if isinstance(schema, dict):
        return {k: _ensure_schema_serializable(v) for k, v in schema.items()}
    elif isinstance(schema, list):
        return [_ensure_schema_serializable(item) for item in schema]
    else:
        return _ensure_serializable(schema)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate LinkML schema from OME XSD")
    parser.add_argument("xsd_path", help="Path to the OME XSD file")
    parser.add_argument("--output", help="Output path for the LinkML schema")
    parser.add_argument("--elements", help="Comma-separated list of top-level elements to include")
    parser.add_argument("--partition", action="store_true", help="Partition the schema into separate files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    top_level_elements = args.elements.split(",") if args.elements else None
    
    generate_linkml_schema(args.xsd_path, args.output, top_level_elements, args.partition)