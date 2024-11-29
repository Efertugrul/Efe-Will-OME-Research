
# **Bioimaging Metadata Schema Generator  (OME RESEARCH)**

### **Project Overview**
This project provides tools and scripts to convert complex bioimaging metadata (e.g., from Excel/CSV files) into structured **LinkML schemas**. The goal is to enable interoperability, validation, and semantic integration of microscopy metadata for research and analysis.

---

## **Key Features**
- **Dimensionality Reduction**: Processes complex hierarchical metadata to simplify and normalize data.
- **Schema Generation**: Automatically generates **LinkML YAML schemas** for structured and semantic data modeling.
- **Data Validation**: Ensures metadata adheres to standardized formats and constraints.
- **Support for Multiple Formats**: Handles Excel and CSV files as input for schema creation.

---

## **Getting Started**

### **Prerequisites**
- Python 3.8+
- Required Python libraries:
  - `pandas`
  - `openpyxl`
  - `pyyaml`

Install dependencies:
```bash
pip install pandas openpyxl pyyaml
```

---

### **Project Structure**
```
📂 project_root
├── 📂 data
│   ├── input.xlsx        # Input Excel file with metadata
│   ├── output.yaml       # Generated LinkML schema
│
├── 📂 src
│   ├── generator.py      # Main script for metadata processing
│   ├── helpers.py        # Utility functions for data cleaning and schema generation
│
├── README.md             # Project documentation
├── requirements.txt      # List of dependencies
```

---

## **Usage**

### **Step 1: Preprocess Metadata**
Run the script to clean and preprocess the metadata file:
```bash
python src/preprocess.py --input data/input.xlsx --output data/cleaned.csv
```

### **Step 2: Generate LinkML Schema**
Use the cleaned metadata to generate a LinkML schema:
```bash
python src/generator.py --input data/cleaned.csv --output data/output.yaml
```



### **LinkML Schema (YAML)**
```yaml
name: MicroscopyMetadata
description: Schema for OME Core vs. NBO Basic Extension OBJECTIVE Hardware Specifications
prefixes:
  linkml: https://w3id.org/linkml/
  xsd: http://www.w3.org/2001/XMLSchema#
default_prefix: microscopy
types:
  float_with_unit:
    base: float
    description: A floating-point number with an optional unit
  boolean:
    base: bool
    description: A true or false value

enums:
  ObjectiveCorrection:
    permissible_values:
      Achro: {}
      Achromat: {}
      Apo: {}
      Apochromat: {}
      Plan: {}
      SuperFluor: {}
      Other: {}

```

---

## **Contributing**
Contributions are welcome! Please follow these steps to contribute:
1. Fork the repository.
2. Create a new feature branch.
3. Commit your changes.
4. Submit a pull request.

---

## **License**
This project is licensed under the MIT License.

---

### **Verification**
- The manually created **reference YAML file** was successfully verified using the LinkML verifier, with no issues found.
- Once the Python scripts are functional, the output YAML from the Excel-to-YAML converter can be directly compared to the reference format using LinkML packages.
- This ensures that the converter's output aligns with the required schema standards.

