import csv
import sys
from collections import defaultdict
from ruamel.yaml import YAML

def parse_csv(file_path):
  
    with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

def determine_multivalued(cardinality):
 
    if not cardinality:
        return False
    return '...' in cardinality or '∞' in cardinality or 'multi' in cardinality.lower()

def main():
    input_csv = "../data/NBO_MicroscopyMetadataSpecifications_OBJECTIVE_v02-10.csv" 
    output_yaml = 'output.yaml' 

    yaml_dict = {
        'id': 'https://example.org/MicroscopyMetadata',
        'name': 'MicroscopyMetadata',
        'description': 'Schema for OME Core vs. NBO Basic Extension OBJECTIVE Hardware Specifications',
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
        },
        'enums': {},
        'slots': {
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
            }
        },
        'classes': {}
    }

    rows = parse_csv(input_csv)

    enums = {}
    for row in rows:
        allowed_values = row['Allowed values'].strip()
        if allowed_values:
            enum_name = row['Complex type'].strip() if row['Complex type'].strip() else row['AttributeName'].strip()
            enum_values = [value.strip() for value in allowed_values.split(',')]
            enums[enum_name] = {value: {} for value in enum_values}

    for enum_name, values in enums.items():
        yaml_dict['enums'][enum_name] = {
            'description': '',
            'permissible_values': values
        }

    for row in rows:
        allowed_values = row['Allowed values'].strip()
        if allowed_values:
            enum_name = row['Complex type'].strip() if row['Complex type'].strip() else row['AttributeName'].strip()
            description = row['Description'].strip()
            if enum_name in yaml_dict['enums']:
                yaml_dict['enums'][enum_name]['description'] = description

    classes = {}
    current_class = None

    for row in rows:
        data_type = row['Data type'].strip()
        attribute_name = row['AttributeName'].strip()
        description = row['Description'].strip()
        tier = row.get('Tier', row.get('\ufeffTier', '')).strip() 
        required = row['Required?'].strip().upper() == 'Y'
        allowed_values = row['Allowed values'].strip()
        complex_type = row['Complex type'].strip()
        cardinality = row['Cardinality/Required?'].strip()

        if data_type == '-':
            current_class = attribute_name
            classes[current_class] = {
                'description': description,
                'attributes': {}
            }
            continue

        if current_class is None:
            continue

        attr = {
            'description': description,
            'required': required,
            'multivalued': determine_multivalued(cardinality),
            'annotations': {
                'tier': int(tier) if tier.isdigit() else tier,
                'M&M': required
            }
        }

        if complex_type:
            corrected_complex_type = complex_type.replace('ManufactuerSpecs', 'ManufacturerSpecs')
            attr['range'] = f'microscopy.{corrected_complex_type}'
        elif allowed_values:
            enum_name = attribute_name
            attr['range'] = f'microscopy.{enum_name}'
        else:
            type_mapping = {
                'string': 'string',
                'float': 'float',
                'boolean': 'boolean'
            }
            attr['range'] = type_mapping.get(data_type, 'string')

        classes[current_class]['attributes'][attribute_name] = attr

    for class_name, class_info in classes.items():
        yaml_dict['classes'][class_name] = class_info

    if 'Objective' in classes and 'Instrument' in classes:
        yaml_dict['classes']['Instrument']['attributes']['Objective'] = {
            'description': 'The Microscope\'s Objective lens consists of a lens, its mount, and any associated parts. It is the part of the imaging system, which forms a primary image of the object, either alone or in conjunction with a tube lens. The Objective typically consists of a compound lens consisting of several simple lenses (elements), usually arranged along a common axis.',
            'range': 'microscopy.Objective',
            'required': True,
            'multivalued': True,
            'annotations': {
                'tier': 1,
                'M&M': True
            }
        }

    for class_info in yaml_dict['classes'].values():
        for attr_name, attr_info in class_info['attributes'].items():
      
            if attr_name in ['WorkingDistance', 'ObjectiveViewField', 'ImageDistance']:
                attr_info['range'] = 'microscopy.float_with_unit'
            if attr_name == 'CalibratedMagnification':
                attr_info['range'] = 'microscopy.float_with_unit'

    for enum_name in yaml_dict['enums']:
        if not yaml_dict['enums'][enum_name]['description']:
            yaml_dict['enums'][enum_name]['description'] = f'Types of {enum_name}'

    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.preserve_quotes = True

    with open(output_yaml, 'w', encoding='utf-8') as outfile:
        yaml.dump(yaml_dict, outfile)

    print(f"YAML schema has been generated and saved to '{output_yaml}'.")

if __name__ == "__main__":
    main()
