import csv
import yaml

def csv_to_linkml(csv_filename, yaml_filename):
    # Initialize the schema dictionary
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
            'Extension_of_Reference': {  # Custom type
                'base': 'string',
                'description': 'Reference to an annotation'
            },
            'Denomination': {  # Custom type
                'base': 'string',
                'description': 'User-defined name type'
            },
            'LSID': {  # Assuming LSID is a string type
                'base': 'string',
                'description': 'Life Science Identifier (LSID)'
            }
        },
        'enums': {},
        'classes': {},
        'slots': {},
        'annotations': {
            'tier': {
                'description': 'Tier level indicating the depth or importance of the attribute',
                'range': 'integer'
            },
            'cardinality': {
                'description': 'Cardinality indicating the multiplicity of the attribute',
                'range': 'string'
            }
        }
    }

    enums = {}
    with open(csv_filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        current_class = None
        
        for row in reader:
            # Skip rows that don't have AttributeName or Description
            if not row.get('AttributeName') and not row.get('Description'):
                continue
            
            tier = row.get('Tier', '').strip()
            required = row.get('Required?', '').strip().lower()
            attribute_name = row.get('AttributeName', '').strip()
            description = row.get('Description', '').strip()
            data_type = row.get('Data type', '').strip()
            allowed_values = row.get('Allowed values', '').strip()
            complex_type = row.get('Complex type', '').strip()
            cardinality = row.get('Cardinality/Required?', '').strip()
            
            # Detect if the row defines a new class
            # Assuming that classes have an AttributeName but no Data type and no Complex type
            if attribute_name and not data_type and not complex_type:
                current_class = attribute_name
                schema['classes'][current_class] = {
                    'description': description,
                    'attributes': {}
                }
                continue
            
            # If there's no current class, skip the row
            if not current_class:
                continue
            
            # Prepare attribute entry
            attr_entry = {
                'description': description
            }
            
            # Handle tier as a separate property
            if tier:
                try:
                    attr_entry['tier'] = int(tier)
                except ValueError:
                    attr_entry['tier'] = tier  # Keep as string if not integer
            
            # Handle cardinality as a separate property
            if cardinality:
                # Determine if multivalued based on cardinality string
                if '...' in cardinality or '∞' in cardinality or 'multiple' in cardinality.lower():
                    attr_entry['multivalued'] = True
                else:
                    attr_entry['multivalued'] = False
                attr_entry['cardinality'] = cardinality
            else:
                attr_entry['multivalued'] = False 
                attr_entry['cardinality'] = 'NULL' 
            
            if required in ['y', 'yes', 'r', 'required']:
                attr_entry['required'] = True
            
            if data_type.lower() == 'enum' and allowed_values:
                enum_name = complex_type if complex_type else f"{attribute_name}Enum"
                # Clean enum values by replacing spaces with underscores
                enum_values = [value.strip().replace(' ', '_') for value in allowed_values.split(',')]
                enums[enum_name] = {
                    'permissible_values': {value: {} for value in enum_values}
                }
                attr_entry['range'] = enum_name
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
                attr_entry['range'] = 'string'  # Default to string if unspecified
            
            # Add attribute to the current class
            schema['classes'][current_class]['attributes'][attribute_name] = attr_entry

    # Add enums to the schema
    schema['enums'] = enums

    # Write the schema to a YAML file
    with open(yaml_filename, 'w', encoding='utf-8') as yamlfile:
        yaml.dump(schema, yamlfile, sort_keys=False, allow_unicode=True)

if __name__ == '__main__':
    csv_filename = 'NBO_MicroscopyMetadataSpecifications_OBJECTIVE_v02-10.csv'
    yaml_filename = 'output.yaml'  # Output LinkML schema file
    csv_to_linkml(csv_filename, yaml_filename)
