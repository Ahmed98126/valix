"""Create Excel templates for the application."""

import os
import pandas as pd
from pathlib import Path

def create_account_mapping_template():
    """Create Excel template for account mappings."""
    # Create DataFrame with sample data
    df = pd.DataFrame({
        "Supplier Name": ["British Gas", "E.ON", "Water Company"],
        "Account Number": ["1234567890", "0987654321", "WATER001"],
        "Unit ID": ["SHOP-001", "OFFICE-101", "UNIT-A5"],
        "Notes": ["Main electricity account", "Office building", "Water supply"]
    })
    
    # Create templates directory if it doesn't exist
    templates_dir = Path("static/templates")
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to Excel
    output_path = templates_dir / "account_mapping_template.xlsx"
    df.to_excel(output_path, index=False)
    
    print(f"Created account mapping template: {output_path}")
    return output_path

if __name__ == "__main__":
    create_account_mapping_template()