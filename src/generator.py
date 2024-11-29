import csv
import yaml

def csv_to_linkml(csv_filename, yaml_filename):
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
            'Extension_of_Reference': {  'base': 'string',
                'description': 'Reference to an annotation'
            },
            'Denomination': { 'base': 'string',
                'description': 'User-defined name type'
            },
            'LSID': {  'base': 'string',
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
            if attribute_name and not data_type and not complex_type:
                current_class = attribute_name
                schema['classes'][current_class] = {
                    'description': description,
                    'attributes': {}
                }
                continue
            
            if not current_class:
                continue
            attr_entry = {
                'description': description
            }
            
            if tier:
                try:
                    attr_entry['tier'] = int(tier)
                except ValueError:
                    attr_entry['tier'] = tier 
            
            if cardinality:
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
                attr_entry['range'] = 'string' 
            schema['classes'][current_class]['attributes'][attribute_name] = attr_entry

    schema['enums'] = enums

    with open(yaml_filename, 'w', encoding='utf-8') as yamlfile:
        yaml.dump(schema, yamlfile, sort_keys=False, allow_unicode=True)

if __name__ == '__main__':
    csv_filename = 'NBO_MicroscopyMetadataSpecifications_OBJECTIVE_v02-10.csv'
    yaml_filename = 'output.yaml' 
    csv_to_linkml(csv_filename, yaml_filename)
