import argparse
import pandas as pd
from ruamel.yaml import YAML
import sys
import os
import re

def parse_arguments():
    parser = argparse.ArgumentParser(description="Convert CSV to LinkML schema.")
    parser.add_argument('--input', '-i', required=True, help='Path to input CSV file.')
    parser.add_argument('--output', '-o', required=True, help='Path to output YAML file.')
    return parser.parse_args()

def sanitize_identifier(value):
    """
    Sanitize identifiers by replacing spaces, hyphens, and other invalid characters with underscores.
    Removes any characters that are not alphanumeric or underscores.
    """
    if isinstance(value, str):
        # Replace spaces and hyphens with underscores
        value = re.sub(r'[ \-]', '_', value.strip())
        # Remove any characters that are not alphanumeric or underscores
        value = re.sub(r'[^\w]', '', value)
        return value
    return value

def correct_class_name(class_name):
    """
    Correct common typographical errors in class names.
    """
    corrections = {
        'ManufactuerSpecs': 'ManufacturerSpecs',
        'manufactuerspecs': 'ManufacturerSpecs',
        'Manufacturer_Specs': 'ManufacturerSpecs'
        # Add more corrections if needed
    }
    return corrections.get(class_name, class_name)
def main():
    args = parse_arguments()
    
    try:
        # Explicitly specify UTF-8 encoding when reading CSV
        df = pd.read_csv(args.input, dtype=str, encoding='utf-8-sig')  # utf-8-sig handles BOM if present
    except UnicodeDecodeError:
        try:
            # Fallback to Windows-1252 if UTF-8 fails
            df = pd.read_csv(args.input, dtype=str, encoding='windows-1252')
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            sys.exit(1)
    # Initialize schema dictionary
    schema = {
        'id': 'https://example.org/MicroscopyMetadata',
        'name': 'MicroscopyMetadata',
        'description': 'Schema for OME Core vs. NBO Basic Extension OBJECTIVE Hardware Specifications',
        'prefixes': {
            'linkml': 'https://w3id.org/linkml/',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
            'microscopy': 'https://example.org/microscopy#'  # Added a prefix for clarity
        },
        'default_prefix': 'microscopy',
        'types': {},
        'enums': {},
        'slots': {},
        'classes': {}
    }

    # Predefined types as per the schema requirements
    predefined_types = {
        'float_with_unit': {
            'base': 'float',
            'description': 'A floating-point number with an optional unit (e.g., 1.27 NA, 60X)'
        },
        'boolean': {
            'base': 'bool',
            'description': 'A true or false value'
        },
        'Extension_of_Reference': {
            'base': 'string',
            'description': 'Reference to an annotation or external resource'
        },
        'Denomination': {
            'base': 'string',
            'description': 'User-defined name type for custom identifiers'
        },
        'LSID': {
            'base': 'string',
            'description': 'Life Science Identifier (LSID) used for unique identification'
        }
    }

    schema['types'].update(predefined_types)

    # Define slots
    schema['slots'] = {
        'tier': {
            'description': 'Tier level indicating the depth or importance',
            'range': 'integer'
        },
        'M&M': {
            'description': 'Indicates if the attribute is required',
            'range': 'boolean'
        },
        'cardinality': {
            'description': 'Cardinality indicating the multiplicity of the attribute',
            'range': 'string'
        },
        'multivalued': {
            'description': 'Indicates if the attribute can have multiple values',
            'range': 'boolean'
        }
    }

    # Initialize variables
    current_class = None
    classes = schema['classes']
    enums = schema['enums']

    # Iterate through each row
    for index, row in df.iterrows():
        # Extract and sanitize each field
        tier = row['Tier'].strip() if pd.notna(row['Tier']) else '1'
        required = row['Required?'].strip().upper() if pd.notna(row['Required?']) else 'N'
        attribute_name_raw = row['AttributeName'].strip() if pd.notna(row['AttributeName']) else None
        description = row['Description'].strip() if pd.notna(row['Description']) else ''
        data_type = row['Data type'].strip() if pd.notna(row['Data type']) else '-'
        allowed_values = row['Allowed values'].strip() if pd.notna(row['Allowed values']) else '-'
        complex_type_raw = row['Complex type'].strip() if pd.notna(row['Complex type']) else '-'
        cardinality = row['Cardinality/Required?'].strip() if pd.notna(row['Cardinality/Required?']) else '-'

        # Skip rows with empty AttributeName
        if not attribute_name_raw:
            print(f"Warning: Skipping row {index + 2} due to empty 'AttributeName'.")
            continue

        # Determine if the row defines a class
        is_class = False
        if data_type == '-' and allowed_values == '-' and complex_type_raw == '-':
            is_class = True
        elif attribute_name_raw.lower() in ['manufactuerspecs', 'manufacturer_specs']:
            is_class = True

        if is_class:
            # Correct typo in class name if necessary
            class_name_corrected = correct_class_name(attribute_name_raw)
            class_name_sanitized = sanitize_identifier(class_name_corrected)
            # Initialize class in schema
            classes[class_name_sanitized] = {
                'description': description,
                'attributes': {}
            }
            current_class = class_name_sanitized
            continue  # Move to next row

        # If not a class, it's an attribute. Ensure that a class has been defined
        if current_class is None:
            print(f"Error: Attribute '{attribute_name_raw}' defined before any class.")
            sys.exit(1)

        # Initialize attribute dictionary
        attribute = {
            'description': description
        }

        # Determine the range and handle enums
        if data_type.lower() == 'enum':
            # Define enum using 'Complex type' as enum name
            enum_name_raw = complex_type_raw
            enum_name = sanitize_identifier(enum_name_raw)
            if not enum_name:
                print(f"Warning: Skipping enum definition for attribute '{attribute_name_raw}' due to empty 'Complex type'.")
                continue
            if enum_name not in enums:
                enums[enum_name] = {
                    'description': f"Types of {enum_name}",
                    'permissible_values': {}
                }
                # Split allowed values by comma and sanitize
                enum_values = [sanitize_identifier(val) for val in allowed_values.split(',')]
                for val in enum_values:
                    if val:  # Ensure value is not empty
                        enums[enum_name]['permissible_values'][val] = {}
            # Set attribute range to the enum
            attribute['range'] = f'microscopy.{enum_name}'
        elif allowed_values != '-' and allowed_values != '':
            # Define enum using 'AttributeName' as enum name
            enum_name_raw = attribute_name_raw
            enum_name = sanitize_identifier(enum_name_raw)
            if enum_name not in enums:
                enums[enum_name] = {
                    'description': f"Types of {enum_name}",
                    'permissible_values': {}
                }
                # Split allowed values by comma and sanitize
                enum_values = [sanitize_identifier(val) for val in allowed_values.split(',')]
                for val in enum_values:
                    if val:
                        enums[enum_name]['permissible_values'][val] = {}
            # Set attribute range to the enum
            attribute['range'] = f'microscopy.{enum_name}'
        elif data_type != '-' and data_type != '':
            # Handle predefined data types or custom types
            if data_type.lower() in ['string', 'float', 'boolean']:
                if data_type.lower() == 'string':
                    attribute['range'] = 'string'
                elif data_type.lower() == 'float':
                    attribute['range'] = 'float'
                elif data_type.lower() == 'boolean':
                    attribute['range'] = 'boolean'
            elif data_type in schema['types']:
                attribute['range'] = data_type
            else:
                # Assume it's a complex type (another class)
                class_ref_corrected = correct_class_name(data_type)
                class_ref_sanitized = sanitize_identifier(class_ref_corrected)
                attribute['range'] = f'microscopy.{class_ref_sanitized}'
        elif complex_type_raw != '-' and complex_type_raw != '':
            # Reference to a complex type (another class)
            class_ref_corrected = correct_class_name(complex_type_raw)
            class_ref_sanitized = sanitize_identifier(class_ref_corrected)
            attribute['range'] = f'microscopy.{class_ref_sanitized}'
        else:
            # Default to string if no type is specified
            attribute['range'] = 'string'

        # Handle multivalued
        if '...' in cardinality:
            attribute['multivalued'] = True
        elif re.search(r'\d+\s*\.\.\.\s*[*\d]+', cardinality):
            # For patterns like '1 ... ∞' or '1...1', etc.
            if '...' in cardinality:
                # Check if upper bound is '*' or a number greater than 1
                upper = cardinality.split('...')[1].strip()
                if upper == '*' or re.match(r'^\d+$', upper):
                    attribute['multivalued'] = True if upper != '1' else False
                else:
                    attribute['multivalued'] = True
            else:
                attribute['multivalued'] = False
        else:
            attribute['multivalued'] = False

        # Handle required
        attribute['required'] = True if required == 'Y' else False

        # Handle annotations for tier and M&M
        try:
            tier_int = int(tier)
        except ValueError:
            tier_int = 1  # Default tier if conversion fails
        attribute['annotations'] = {
            'tier': tier_int,
            'M&M': True if required == 'Y' else False
        }

        # Assign to the current class
        classes[current_class]['attributes'][attribute_name_raw] = attribute

    # Add predefined enums if not already defined
    predefined_enums = {
        'ObjectiveCorrection': {
            'description': 'Types of optical corrections available for objectives',
            'permissible_values': {
                'Achro': {},
                'Achromat': {},
                'Achroplan': {},
                'Acroplan': {},
                'Apo': {},
                'Apochromat': {},
                'C_Achroplan': {},
                'EF': {},
                'Fl': {},
                'Fluar': {},
                'Fluor': {},
                'Fluotar': {},
                'Lambda': {},
                'N': {},
                'Neofluar': {},
                'NPL': {},
                'Pl': {},
                'Plan': {},
                'Plano': {},
                'PlanApo': {},
                'PlanApochromat': {},
                'PlanFluor': {},
                'PlanNeofluar': {},
                'SuperFluor': {},
                'UPLAN': {},
                'UPlanApo': {},
                'UPlanFl': {},
                'UV': {},
                'VioletCorrected': {},
                'Other': {}
            }
        },
        'ImmersionTypeList': {
            'description': 'Types of immersion liquids used between the lens and specimen',
            'permissible_values': {
                'Air': {},
                'Dipping': {},
                'Glycerol': {},
                'Multi': {},
                'Mineral_Oil': {},
                'Silicone_Oil': {},
                'Water': {},
                'Other': {}
            }
        },
        'ContrastModulationPlate': {
            'description': 'Types of contrast modulation plates available in objectives',
            'permissible_values': {
                'None': {},
                'Ph1': {},
                'Ph2': {},
                'Ph3': {},
                'Hoffman': {},
                'VAREL': {},
                'Other': {}
            }
        },
        'ObjectiveLightType': {
            'description': 'Types of light applications an objective is designed for',
            'permissible_values': {
                'Infrared': {},
                'Ultraviolet': {},
                'Visible': {}
            }
        },
        'CorrectionCollarTypeList': {
            'description': 'Types of correction collars available for objectives',
            'permissible_values': {
                'Coverglass_Thickness': {},
                'Immersion_Liquid': {},
                'Numerical_Aperture': {},
                'Temperature': {},
                'Multi': {}
            }
        },
        'DippingType': {
            'description': 'Types of dipping mediums compatible with objectives',
            'permissible_values': {
                'Organic_based': {},  
                'Water_based': {},
                'Other': {}
            }
        },
        'PhaseContrastDesignationType': {
            'description': 'Designations for phase contrast objectives',
            'permissible_values': {
                'Phase': {},
                'PHACO': {},
                'PC': {},
                'PhL': {},
                'Ph1': {},
                'Ph2': {},
                'Ph3': {},
                'Ph4': {},
                'DL': {},
                'DLL': {},
                'DM': {},
                'ADL': {},
                'PL': {},
                'PLL': {},
                'PM': {},
                'PH': {},
                'NL': {},
                'NM': {},
                'BM': {},
                'NH': {}
            }
        }
    }

    # Merge predefined enums with those defined from CSV
    for enum_name, enum_def in predefined_enums.items():
        if enum_name not in enums:
            enums[enum_name] = enum_def

    # Initialize YAML writer
    yaml_writer = YAML()
    yaml_writer.indent(mapping=2, sequence=4, offset=2)
    yaml_writer.width = 4096
    yaml_writer.allow_unicode = True  # Enable Unicode support

    try:
        with open(args.output, 'w', encoding='utf-8') as outfile:
            yaml_writer.dump(schema, outfile)
        print(f"LinkML schema has been successfully generated at '{args.output}'")
    except Exception as e:
        print(f"Error writing YAML file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
