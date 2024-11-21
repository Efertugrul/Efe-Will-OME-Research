
# **Bioimaging Metadata Schema Generator (OME RESEARCH METADATA SPECS)**

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

---


### **Generated LinkML Schema (YAML)  (Subject to Change)**
```yaml
id: microscopy_metadata
name: MicroscopyMetadata
description: Schema for structured microscopy metadata
classes:
  Microscope:
    description: Represents a microscope and its components
    attributes:
      microscope_stand:
        description: The stand holding the microscope components
        range: string
        required: true
      objective_magnification:
        description: The magnification of the objective lens
        range: integer
        required: true
        values:
          - 10
          - 20
          - 40
```



## **License**
This project is licensed under the MIT License.
