# csv_to_linkml_new_file.py

import csv
from collections import defaultdict
from ruamel.yaml import YAML
import os
import sys

def parse_csv(file_path):

    with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        reader.fieldnames = [fn.strip() for fn in reader.fieldnames]
        return list(reader)

def determine_multivalued(cardinality):
    if not cardinality:
        return False
    return '...' in cardinality or '∞' in cardinality or 'multi' in cardinality.lower()

def correct_typos(text):
    if not text:
        return text
    corrections = {
        'ManufactuerSpecs': 'ManufacturerSpecs',
        'FIlterID': 'FilterID',
        'ΜanufactuerSpecs': 'ManufacturerSpecs',  
        'Filtr Wheel': 'Filter Wheel',
        'Beamsplitter is': 'Beamsplitter',
        'componewnt': 'component',
        'float with unit:none': 'float_with_unit',
        'integer with unit:none': 'integer_with_unit',
        'float with unit:DiameterUnit [default mm]': 'float_with_unit',
        'float with unit:ThicknessUnit': 'float_with_unit',
        'float with unit:AngleOfIncidenceUnit': 'float_with_unit',
        'float with unit:WavelengthUnit': 'float_with_unit',
        'positiveFloat with unit:WavelengthUnit': 'positiveFloat_with_unit',
        'percentFraction with unit:none': 'percentFraction_with_unit',
        'LSID': 'LSID',
        'Denomination': 'Denomination',
        'Extension of Reference': 'Extension_of_Reference',
        'FileAnnotation': 'FileAnnotation',
        'nonNegativeFloat': 'nonNegativeFloat',
        'positiveFloat_with_unit': 'positiveFloat_with_unit'
    }
    for typo, correction in corrections.items():
        text = text.replace(typo, correction)
    return text

def convert_csv_to_linkml_new_file(input_csv, output_yaml):
    yaml_dict = {
        'id': 'https://example.org/MicroscopyMetadata',
        'name': 'MicroscopyMetadata',
        'description': 'Schema for Microscope Hardware Specifications',
        'prefixes': {
            'linkml': 'https://w3id.org/linkml/',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
            'microscopy': 'https://example.org/microscopy#'
        },
        'default_prefix': 'microscopy',
        'types': {
            'float_with_unit': {
                'base': 'float',
                'description': 'A floating-point number with an optional unit (e.g., 1.27 NA, 60X)'
            },
            'integer_with_unit': {
                'base': 'integer',
                'description': 'An integer with an optional unit (e.g., 100 mm)'
            },
            'percentFraction_with_unit': {
                'base': 'float',
                'description': 'A fractional value representing a percentage (0.0 to 1.0) with an optional unit'
            },
            'positiveFloat_with_unit': {
                'base': 'float',
                'description': 'A positive floating-point number with an optional unit'
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
            },
            'nonNegativeFloat': {
                'base': 'float',
                'description': 'A floating-point number that is zero or positive'
            },
            'Element': {
                'base': 'string',
                'description': 'A generic element type'
            },
            'FileAnnotation': {
                'base': 'string',
                'description': 'Reference to a file annotation'
            }
        },
        'enums': {},
        'slots': {
            'tier': {
                'description': 'Tier level indicating the depth or importance',
                'range': 'integer'
            },
            'Required': {
                'description': 'Indicates if the attribute is required',
                'range': 'boolean'
            },
            'cardinality': {
                'description': 'Cardinality indicating the multiplicity of the attribute',
                'range': 'string'
            }
        },
        'classes': {}
    }

    rows = parse_csv(input_csv)

    required_headers = ['Tier', 'Required?', 'AttributeName', 'Description', 'Data type', 'Allowed values', 'Complex type', 'Cardinality/Required?']
    for header in required_headers:
        if header not in rows[0]:
            sys.exit(1)

    enums = {}
    for idx, row in enumerate(rows, start=2):  
        allowed_values = row.get('Allowed values', '').strip()
        if allowed_values:
            enum_name = row.get('Complex type', '').strip()
            if not enum_name:
                enum_name = row.get('AttributeName', '').strip()
            enum_name = correct_typos(enum_name)
            if not enum_name:
                continue
            enum_values = [value.strip() for value in allowed_values.split(',')]
            enums[enum_name] = {value: {} for value in enum_values}

    for enum_name, values in enums.items():
        yaml_dict['enums'][enum_name] = {
            'description': '',  
            'permissible_values': values
        }

    for idx, row in enumerate(rows, start=2):
        allowed_values = row.get('Allowed values', '').strip()
        if allowed_values:
            enum_name = row.get('Complex type', '').strip()
            if not enum_name:
                enum_name = row.get('AttributeName', '').strip()
            enum_name = correct_typos(enum_name)
            description = row.get('Description', '').strip()
            if enum_name in yaml_dict['enums']:
                yaml_dict['enums'][enum_name]['description'] = description

    classes = {}
    current_class = None

    for idx, row in enumerate(rows, start=2):
        data_type = (row.get('Data type') or '').strip()
        attribute_name = (row.get('AttributeName') or '').strip()
        description = (row.get('Description') or '').strip()
        tier = (row.get('Tier') or '').strip()
        required = (row.get('Required?') or '').strip().upper() == 'Y'
        allowed_values = (row.get('Allowed values') or '').strip()
        complex_type = (row.get('Complex type') or '').strip()
        cardinality = (row.get('Cardinality/Required?') or '').strip()

        if data_type == '-':
            current_class = attribute_name
            if not current_class:
                continue
            classes[current_class] = {
                'description': description,
                'attributes': {}
            }
            continue

        if not current_class:
            continue  

        attr = {
            'description': description,
            'required': required,
            'multivalued': determine_multivalued(cardinality),
            'annotations': {
                'tier': int(tier) if tier.isdigit() else tier,
                'Required': required
            }
        }

        if complex_type:
            corrected_complex_type = correct_typos(complex_type)
            attr['range'] = f'microscopy.{corrected_complex_type}'
        elif allowed_values:
            enum_name = attribute_name
            enum_name = correct_typos(enum_name)
            if enum_name not in yaml_dict['enums']:
                attr['range'] = 'string'
            else:
                attr['range'] = f'microscopy.{enum_name}'
        else:
            type_mapping = {
                'string': 'string',
                'enum': 'string',  
                'float_with_unit': 'microscopy.float_with_unit',
                'integer_with_unit': 'microscopy.integer_with_unit',
                'positivefloat_with_unit': 'microscopy.positiveFloat_with_unit',
                'float_with_unit_diameterunit_default_mm': 'microscopy.float_with_unit',
                'float_with_unit_thicknessunit': 'microscopy.float_with_unit',
                'float_with_unit_angleofincidenceunit': 'microscopy.float_with_unit',
                'float_with_unit_wavelengthunit': 'microscopy.float_with_unit',
                'positivefloat_with_unit_wavelengthunit': 'microscopy.positiveFloat_with_unit',
                'percentfraction_with_unit_none': 'microscopy.percentFraction_with_unit',
                'lsid': 'microscopy.LSID',
                'denomination': 'microscopy.Denomination',
                'extension_of_reference': 'microscopy.Extension_of_Reference',
                'nonnegativedouble': 'microscopy.nonNegativeFloat',
                'element': 'microscopy.Element',
                'fileannotation': 'microscopy.FileAnnotation'
            }
            key = data_type.lower().replace(' ', '_').replace(':', '_').replace('[default_mm]', '').replace('/', '_').replace('-', '_')
            attr['range'] = type_mapping.get(key, 'string')

        corrected_attribute_name = correct_typos(attribute_name)
        if not corrected_attribute_name:
            continue
        classes[current_class]['attributes'][corrected_attribute_name] = attr

    for class_name, class_info in classes.items():
        corrected_class_name = correct_typos(class_name)
        yaml_dict['classes'][corrected_class_name] = class_info

    for enum_name, enum_info in yaml_dict['enums'].items():
        if not enum_info['description']:
            enum_info['description'] = f'Types of {enum_name}'

    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.preserve_quotes = True

    try:
        with open(output_yaml, 'w', encoding='utf-8') as outfile:
            yaml.dump(yaml_dict, outfile)
        print(f"LinkML schema has been successfully generated and saved to '{output_yaml}'.")
    except Exception as e:
        sys.exit(1)

    return yaml_dict  

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert cleaned CSV to LinkML schema.")
    parser.add_argument('-i', '--input_csv', help="Path to the cleaned CSV file.", required=True)
    parser.add_argument('-o', '--output_yaml', help="Desired path for the output LinkML YAML schema.", required=True)

    args = parser.parse_args()

    if not os.path.exists(args.input_csv):
        sys.exit(1)

    try:
        convert_csv_to_linkml_new_file(args.input_csv, args.output_yaml)
    except Exception as e:
        sys.exit(1)
