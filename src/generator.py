import csv
import yaml
import re
import pandas as pd
def detect_delimiter(sample_bytes):
  
    try:
        dialect = csv.Sniffer().sniff(sample_bytes, delimiters=[',', ';', '\t', '|'])
        return dialect.delimiter
    except csv.Error:
        return ',' 

def csv_to_linkml(csv_filename, yaml_filename):
    """
    Transforms the input CSV into the desired LinkML schema, handling multi-line descriptions,
    assigning 'Tier' and 'Required?' (as 'M&M') to each attribute in their respective classes.

    Parameters:
    - csv_filename: Path to the input CSV file.
    - yaml_filename: Path to save the transformed YAML schema.
    """
    schema = {
        'id': 'https://example.org/MicroscopyMetadata',
        'name': 'MicroscopyMetadata',
        'description': 'Schema for OME Core vs. NBO Basic Extension OBJECTIVE Hardware Specifications',
        'prefixes': {
            'linkml': 'https://w3id.org/linkml/',
            'xsd': 'http://www.w3.org/2001/XMLSchema#'
        },
        'default_prefix': 'microscopy',
        'types': {
            'float_with_unit': {
                'base': 'float',
                'description': 'A floating-point number with an optional unit'
            },
            'boolean': {
                'base': 'bool',
                'description': 'A true or false value'
            },
            'Extension_of_Reference': {  
                'base': 'string',
                'description': 'Reference to an annotation'
            },
            'Denomination': { 
                'base': 'string',
                'description': 'User-defined name type'
            },
            'LSID': {  
                'base': 'string',
                'description': 'Life Science Identifier (LSID)'
            }
        },
        'enums': {},
        'classes': {},
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
            },
            'multivalued': {
                'description': 'Indicates if the attribute can have multiple values',
                'range': 'boolean'
            }
        }
    }

    enums = {}
    with open(csv_filename, 'r', encoding='utf-8') as csvfile:
        sample = csvfile.read(1024)
        delimiter = detect_delimiter(sample)
        csvfile.seek(0)

        reader = csv.DictReader(csvfile, delimiter=delimiter)
        current_class = None

        for row_num, row in enumerate(reader, start=2): 
            tier = row.get('\ufeffTier', '').strip()
            required = row.get('Required?', '').strip().lower()
            attribute_name = row.get('AttributeName', '').strip()
            description = row.get('Description', '').strip()
            data_type = row.get('Data type', '').strip()
            allowed_values = row.get('Allowed values', '').strip()
            complex_type = row.get('Complex type', '').strip()
            cardinality = row.get('Cardinality/Required?', '').strip()


            if attribute_name and (data_type.strip() == '-' or not data_type.strip()) and not complex_type:
                current_class = attribute_name
                schema['classes'][current_class] = {
                    'description': description,
                    'attributes': {}
                }
                if tier.isdigit():
                    schema['classes'][current_class]['tier'] = int(tier)
                elif tier:
                    schema['classes'][current_class]['tier'] = tier
                else:
                    schema['classes'][current_class]['tier'] = None
                print(f"Detected Class: '{current_class}' with Tier='{schema['classes'][current_class]['tier']}'")
                continue

            if attribute_name and data_type.strip() == '-' and complex_type:
                if tier.isdigit():
                    tier_value = int(tier)
                elif tier:
                    tier_value = tier
                else:
                    tier_value = None

                attr_entry = {
                    'description': description,
                    'M&M': required in ['y', 'yes', 'r', 'required'],
                    'tier': tier_value,
                    'range': complex_type
                }

                if cardinality:
                    attr_entry['cardinality'] = cardinality
                    attr_entry['multivalued'] = '...' in cardinality or '∞' in cardinality or 'multiple' in cardinality.lower()
                else:
                    attr_entry['cardinality'] = 'NULL'
                    attr_entry['multivalued'] = False
                if current_class:
                    schema['classes'][current_class]['attributes'][attribute_name] = attr_entry
                    print(f"Added Attribute with Complex Type: '{attribute_name}' to Class '{current_class}'")
                else:
                    print(f"Warning: Attribute '{attribute_name}' found before any class definition. Skipping.")
                continue

            if attribute_name and data_type.strip() != '-':

                if tier.isdigit():
                    tier_value = int(tier)
                elif tier:
                    tier_value = tier
                else:
                    tier_value = None

                attr_entry = {
                    'description': description,
                    'M&M': required in ['y', 'yes', 'r', 'required'],
                    'tier': tier_value
                }

                if cardinality:
                    attr_entry['cardinality'] = cardinality
                    attr_entry['multivalued'] = '...' in cardinality or '∞' in cardinality or 'multiple' in cardinality.lower()
                else:
                    attr_entry['cardinality'] = 'NULL'
                    attr_entry['multivalued'] = False

                if data_type.lower() == 'enum' and allowed_values:
                    enum_name = complex_type if complex_type else f"{attribute_name}Enum"
                    enum_values = [value.strip().replace(' ', '_') for value in allowed_values.split(',')]
                    enums[enum_name] = {
                        'permissible_values': {value: {} for value in enum_values}
                    }
                    attr_entry['range'] = enum_name
                    print(f"Detected Enum: '{enum_name}' with Values: {enum_values}")
                elif 'float' in data_type.lower():
                    attr_entry['range'] = 'float_with_unit'
                elif data_type.lower() == 'boolean':
                    attr_entry['range'] = 'boolean'
                elif data_type.lower() == 'lsid':
                    attr_entry['range'] = 'LSID'
                elif data_type.lower() == 'denomination':
                    attr_entry['range'] = 'Denomination'
                elif data_type.lower() == 'extension of reference':
                    attr_entry['range'] = 'Extension_of_Reference'
                else:
                    attr_entry['range'] = 'string'

                if current_class:
                    schema['classes'][current_class]['attributes'][attribute_name] = attr_entry
                    print(f"Added Regular Attribute: '{attribute_name}' to Class '{current_class}' with Tier='{tier_value}' and M&M='{attr_entry['M&M']}'")
                else:
                    print(f"Warning: Attribute '{attribute_name}' found before any class definition. Skipping.")
                continue

        schema['enums'] = enums

        with open(yaml_filename, 'w', encoding='utf-8') as yamlfile:
            yaml.dump(schema, yamlfile, sort_keys=False, allow_unicode=True)

        print(f"\nLinkML schema successfully created and saved to '{yaml_filename}'.")

if __name__ == '__main__':
    csv_filename = 'NBO_MicroscopyMetadataSpecifications_OBJECTIVE_v02-10.csv' 
    yaml_filename = 'output2.yaml'
    csv_to_linkml(csv_filename, yaml_filename)
