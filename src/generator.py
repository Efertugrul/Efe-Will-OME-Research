import pandas as pd
#Subject to change
def preprocess_and_normalize(file_path):
    df = pd.read_excel(file_path, sheet_name=0, engine="openpyxl")

    df["Tier"] = df["Tier"].fillna(method="ffill")
    df["Description"] = df["Description"].fillna("") 
    parent_class = None
    normalized_data = []

    for _, row in df.iterrows():
        tier = row["Tier"]
        description = row["Description"]
        data_type = row.get("Data type", "string")
        allowed_values = row.get("Allowed values", None)
        cardinality = row.get("Cardinality/Required?", None)

        if tier.isnumeric(): 
            parent_class = description.strip()
            normalized_data.append({
                "Class": parent_class,
                "Parent Class": None,
                "Description": description,
                "Attribute": None,
                "Data Type": None,
                "Cardinality": None,
                "Allowed Values": None,
            })
        else:
            normalized_data.append({
                "Class": parent_class,
                "Parent Class": None,
                "Description": description,
                "Attribute": description.strip(),
                "Data Type": data_type.strip() if isinstance(data_type, str) else "string",
                "Cardinality": cardinality.strip() if isinstance(cardinality, str) else None,
                "Allowed Values": allowed_values.strip() if isinstance(allowed_values, str) else None,
            })
    normalized_df = pd.DataFrame(normalized_data)
    return normalized_df


def generate_linkml_from_normalized(normalized_df, output_file):
    from yaml import safe_dump

    schema = {
        "id": "microscopy_metadata",
        "name": "MicroscopyMetadata",
        "description": "Reduced schema for microscopy metadata",
        "classes": {},
    }

    for _, row in normalized_df.iterrows():
        class_name = row["Class"]
        if class_name not in schema["classes"]:
            schema["classes"][class_name] = {
                "description": row["Description"],
                "attributes": {}
            }
        if pd.notna(row["Attribute"]):
            attr_name = row["Attribute"].lower().replace(" ", "_")
            schema["classes"][class_name]["attributes"][attr_name] = {
                "description": row["Description"],
                "range": row["Data Type"],
                "required": row["Cardinality"] == "R", 
            }
            if pd.notna(row["Allowed Values"]):
                schema["classes"][class_name]["attributes"][attr_name]["values"] = row["Allowed Values"].split(",")

    with open(output_file, "w") as f:
        safe_dump(schema, f, sort_keys=False)

    print(f"Schema saved to {output_file}")

input_file = "../data/NBO_MicroscopyMetadataSpecifications_OBJECTIVE_v02-10.xlsx"
output_file = "../data/generated_schema.yaml"
normalized_df = preprocess_and_normalize(input_file)
generate_linkml_from_normalized(normalized_df, output_file)
