import csv
import sys
from collections import defaultdict
from ruamel.yaml import YAML

def parse_csv(file_path):
    """
    Reads the CSV file and returns a list of dictionaries,
    one for each row, keyed by column headers (the same as the raw CSV).
    """
    with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

def determine_multivalued(cardinality):
    """
    Returns True if the CSV row's 'Cardinality/Required?' suggests a multi-valued slot
    (e.g. '1..∞', '1 ... ∞', 'Many', 'multi', etc.).
    Adjust or expand logic as needed.
    """
    if not cardinality:
        return False
    cardinality_lower = cardinality.lower()
    return ('∞' in cardinality_lower or '...' in cardinality_lower or 'multi' in cardinality_lower or 'many' in cardinality_lower)

def main():
    input_csv = "../data/mirrorDev_correct.csv" 
    output_yaml = "mirroringdevice_schema.yaml"

  
    yaml_dict = {
        'id': 'https://example.org/MicroscopyMetadata',
        'name': 'MicroscopyMetadata_MirroringDevice',
        'description': 'Schema for OME Core vs. NBO Basic Extension: MirroringDevice & related hardware',
        'prefixes': {
            'linkml': 'https://w3id.org/linkml/',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
            'microscopy': 'https://example.org/microscopy#'
        },
        'default_prefix': 'microscopy',
        'types': {
            'float_with_unit': {
                'base': 'float',
                'description': 'A floating-point number that may include a unit (e.g., 45 deg, 1.5 mm, etc.)'
            },
            'percentFraction_with_unit_none': {
                'base': 'float',
                'description': 'A fraction between 0.0 and 1.0, representing e.g. transmittance or reflectance.'
            },
            'positiveFloat_with_unit': {
                'base': 'float',
                'description': 'A positive floating-point number with an associated wavelength or length unit.'
            },
            'Extension_of_Reference': {
                'base': 'string',
                'description': 'A reference to some annotation or external resource'
            },
            'LDIS': {
                'base': 'string',
                'description': 'Potential custom type for an LSID or LDIS, as indicated by your CSV'
            }
        },
        'enums': {},
        'slots': {
            'Tier': {
                'description': 'Tier level indicating the depth or importance.',
                'range': 'integer'
            },
            'M&M': {
                'description': 'Indicates if the attribute is required (Y/N).',
                'range': 'boolean'
            },
            'Cardinality': {
                'description': 'Cardinality indicating the multiplicity of the attribute (e.g., 1..∞).',
                'range': 'string'
            }
        },
        'classes': {}
    }

    rows = parse_csv(input_csv)


    enums_dict = defaultdict(set)  
    for row in rows:
        allowed_vals = row.get("Allowed values", "").strip()
        if allowed_vals:
            splitted = [val.strip() for val in allowed_vals.split(",") if val.strip()]
            enum_name = row.get("Complex type", "").strip() or row.get("Data type", "").strip()
            if enum_name and splitted:
                for val in splitted:
                    enums_dict[enum_name].add(val)

    for enum_name, values in enums_dict.items():
        if not enum_name:
            enum_name = "UnnamedEnum"
        yaml_dict['enums'][enum_name] = {
            'description': f'Enum for {enum_name}',
            'permissible_values': {val: {} for val in sorted(values)}
        }


    classes = {}
    current_class = None

   
    for row in rows:
        data_type = row.get("Data type", "").strip()
        desc = row.get("Description", "").strip()
        cardinality = row.get("Cardinality/Required?", "").strip()
        mm = row.get("M&M", "").upper().strip() 

        if data_type == '-':
 
            possible_class_names = []
            for col_idx in ["Tier","M&M","Description","Data type","Allowed values","Complex type"]:
                pass

       
            row_values = list(row.values())
            class_name = None
            for val in row_values:
                val_str = (val or "").strip()
            
                if val_str and val_str not in [
                    "-", "R", "Y", "e,e", "Substitution", "choose one child from the list below",
                    "substitution group (choose one or more)"
                ] and len(val_str) < 80:
                    class_name = val_str
                    break
            if not class_name:
                class_name = "UnnamedClass"

            classes[class_name] = {
                'description': desc if desc else f"Auto-generated class for {class_name}",
                'attributes': {}
            }
            current_class = class_name
            continue

        if current_class is not None:
           
            attr_name = None

         
            for col_key in ["Complex type", "Data type", "Allowed values"]:
                candidate = row.get(col_key, "").strip()
       
                if candidate and 1 < len(candidate) < 60:
                    attr_name = candidate
                    break

            if not attr_name:
          
                attr_name = f"{current_class}_attr_{row.get('Tier','')}"

            is_required = (mm == 'Y')

            attr_info = {
                'description': desc,
                'required': is_required,
                'multivalued': determine_multivalued(cardinality),
                'annotations': {
                    'cardinality': cardinality,  
                    'M&M': mm
                }
            }

            
            dt_lower = data_type.lower()
            if "enum" in dt_lower:
                possible_enum = row.get("Complex type", "").strip() or row.get("Data type", "").strip()
                if possible_enum in yaml_dict['enums']:
                    attr_info['range'] = f"microscopy.{possible_enum}"
                else:
                    attr_info['range'] = "string"
            elif "float with unit" in dt_lower:
                attr_info['range'] = "microscopy.float_with_unit"
            elif "percentfraction with unit:none" in dt_lower:
                attr_info['range'] = "microscopy.percentFraction_with_unit_none"
            elif "positivefloat with unit" in dt_lower:
                attr_info['range'] = "microscopy.positiveFloat_with_unit"
            elif "extension of reference" in dt_lower:
                attr_info['range'] = "microscopy.Extension_of_Reference"
            elif "ldis" in dt_lower:
                attr_info['range'] = "microscopy.LDIS"
            else:
                attr_info['range'] = "string"

            classes[current_class]['attributes'][attr_name] = attr_info

    for cls_name, cls_obj in classes.items():
        yaml_dict['classes'][cls_name] = cls_obj

   
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.preserve_quotes = True

    with open(output_yaml, 'w', encoding='utf-8') as outfile:
        yaml.dump(yaml_dict, outfile)

    print(f"[INFO] Generated LinkML schema: {output_yaml}")

if __name__ == "__main__":
    main()
