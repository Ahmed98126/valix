"""Generate a comprehensive test Excel file for validation testing.

This creates an Excel file with various scenarios:
- Invoices for units with leases (should be Valid)
- Invoices for units during vacancy periods (should be Invalid)
- Invoices with different daily rates (to test determinations)
- Invoices for units ending in '00' (Landlord Supply)
- Invoices with various amounts and periods

Usage:
    python scripts/generate_test_excel.py [--output=test_batch.xlsx] [--count=50]
"""

import sys
import random
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.models import Unit, Lease, UnitTimeline


def get_units_and_timelines():
    """Get units and their vacancy/occupied periods."""
    init_db()
    
    with get_session() as session:
        units = session.query(Unit).all()
        if not units:
            raise ValueError("No units found. Load sample data first: python scripts/load_sample_data.py")
        
        # Generate timeline for units
        from app.validation import generate_unit_timeline
        generate_unit_timeline(session)
        
        # Get timelines for each unit
        unit_data = {}
        for unit in units:
            timelines = session.query(UnitTimeline).filter(
                UnitTimeline.unit_id == unit.unit_id
            ).order_by(UnitTimeline.period_start).all()
            
            unit_data[unit.unit_id] = {
                "unit": unit,
                "timelines": timelines
            }
        
        return unit_data


def generate_test_invoices(unit_data, count=50):
    """Generate test invoices with various scenarios."""
    invoices = []
    suppliers = ["Test Energy Ltd", "Water Systems Inc", "Gas Provider Co", "Electricity Corp"]
    utilities = ["Electricity", "Gas", "Water"]
    
    today = date.today()
    invoice_counter = 1
    
    # Scenario 1: Invoices during occupied periods (should be Valid)
    occupied_count = count // 3
    for i in range(occupied_count):
        unit_id = random.choice(list(unit_data.keys()))
        timelines = unit_data[unit_id]["timelines"]
        
        # Find an occupied period
        occupied_periods = [t for t in timelines if t.status == "occupied"]
        if not occupied_periods:
            continue
        
        period = random.choice(occupied_periods)
        period_start = period.period_start
        period_end = period.period_end if period.period_end else today - timedelta(days=30)
        
        # Create invoice within this occupied period
        if period_end - period_start < timedelta(days=30):
            continue
        
        invoice_start = period_start + timedelta(days=random.randint(0, max(1, (period_end - period_start).days - 30)))
        invoice_end = invoice_start + timedelta(days=random.randint(28, 31))
        
        if invoice_end > period_end:
            invoice_end = period_end
        
        gross_amount = Decimal(str(round(random.uniform(100, 500), 2)))
        
        invoices.append({
            "Invoice Number": f"TEST-OCC-{invoice_counter:04d}",
            "Supplier Name": random.choice(suppliers),
            "Property or Unit reference": unit_id,
            "Period From Date": invoice_start.strftime("%d/%m/%Y"),
            "Period To Date": invoice_end.strftime("%d/%m/%Y"),
            "Invoice Date": (invoice_end + timedelta(days=5)).strftime("%d/%m/%Y"),
            "Gross Inv Amt": float(gross_amount),
            "Net": float(gross_amount * Decimal("0.95")),
            "VAT": float(gross_amount * Decimal("0.05")),
            "Utility Type": random.choice(utilities),
            "Currency": "GBP"
        })
        invoice_counter += 1
    
    # Scenario 2: Invoices during vacancy periods (should be Invalid)
    vacancy_count = count // 3
    for i in range(vacancy_count):
        unit_id = random.choice(list(unit_data.keys()))
        timelines = unit_data[unit_id]["timelines"]
        
        # Find a vacancy period
        vacancy_periods = [t for t in timelines if t.status == "vacant"]
        if not vacancy_periods:
            continue
        
        period = random.choice(vacancy_periods)
        period_start = period.period_start
        period_end = period.period_end if period.period_end else today - timedelta(days=30)
        
        # Create invoice within this vacancy period
        if period_end - period_start < timedelta(days=30):
            continue
        
        invoice_start = period_start + timedelta(days=random.randint(0, max(1, (period_end - period_start).days - 30)))
        invoice_end = invoice_start + timedelta(days=random.randint(28, 31))
        
        if invoice_end > period_end:
            invoice_end = period_end
        
        gross_amount = Decimal(str(round(random.uniform(100, 500), 2)))
        
        invoices.append({
            "Invoice Number": f"TEST-VAC-{invoice_counter:04d}",
            "Supplier Name": random.choice(suppliers),
            "Property or Unit reference": unit_id,
            "Period From Date": invoice_start.strftime("%d/%m/%Y"),
            "Period To Date": invoice_end.strftime("%d/%m/%Y"),
            "Invoice Date": (invoice_end + timedelta(days=5)).strftime("%d/%m/%Y"),
            "Gross Inv Amt": float(gross_amount),
            "Net": float(gross_amount * Decimal("0.95")),
            "VAT": float(gross_amount * Decimal("0.05")),
            "Utility Type": random.choice(utilities),
            "Currency": "GBP"
        })
        invoice_counter += 1
    
    # Scenario 3: Invoices for units ending in '00' (Landlord Supply)
    landlord_units = [uid for uid in unit_data.keys() if uid.endswith('00')]
    if landlord_units:
        for i in range(min(5, count // 5)):
            unit_id = random.choice(landlord_units)
            invoice_start = today - timedelta(days=random.randint(60, 90))
            invoice_end = invoice_start + timedelta(days=random.randint(28, 31))
            
            gross_amount = Decimal(str(round(random.uniform(200, 800), 2)))
            
            invoices.append({
                "Invoice Number": f"TEST-LS-{invoice_counter:04d}",
                "Supplier Name": random.choice(suppliers),
                "Property or Unit reference": unit_id,
                "Period From Date": invoice_start.strftime("%d/%m/%Y"),
                "Period To Date": invoice_end.strftime("%d/%m/%Y"),
                "Invoice Date": (invoice_end + timedelta(days=5)).strftime("%d/%m/%Y"),
                "Gross Inv Amt": float(gross_amount),
                "Net": float(gross_amount * Decimal("0.95")),
                "VAT": float(gross_amount * Decimal("0.05")),
                "Utility Type": random.choice(utilities),
                "Currency": "GBP"
            })
            invoice_counter += 1
    
    # Scenario 4: Invoices with different daily rates (to test determinations)
    remaining = count - len(invoices)
    for i in range(remaining):
        unit_id = random.choice(list(unit_data.keys()))
        
        # Create invoice with specific daily rate
        days = random.randint(28, 31)
        daily_rate_target = random.choice([2, 5, 12])  # <£4, £4-£10, >£10
        gross_amount = Decimal(str(round(daily_rate_target * days, 2)))
        
        invoice_start = today - timedelta(days=random.randint(60, 120))
        invoice_end = invoice_start + timedelta(days=days)
        
        invoices.append({
            "Invoice Number": f"TEST-RATE-{invoice_counter:04d}",
            "Supplier Name": random.choice(suppliers),
            "Property or Unit reference": unit_id,
            "Period From Date": invoice_start.strftime("%d/%m/%Y"),
            "Period To Date": invoice_end.strftime("%d/%m/%Y"),
            "Invoice Date": (invoice_end + timedelta(days=5)).strftime("%d/%m/%Y"),
            "Gross Inv Amt": float(gross_amount),
            "Net": float(gross_amount * Decimal("0.95")),
            "VAT": float(gross_amount * Decimal("0.05")),
            "Utility Type": random.choice(utilities),
            "Currency": "GBP"
        })
        invoice_counter += 1
    
    return invoices


def create_excel_file(invoices, output_path):
    """Create Excel file with proper formatting."""
    df = pd.DataFrame(invoices)
    
    # Reorder columns to match expected format
    column_order = [
        "Invoice Number",
        "Supplier Name",
        "Property or Unit reference",
        "Period From Date",
        "Period To Date",
        "Invoice Date",
        "Gross Inv Amt",
        "Net",
        "VAT",
        "Utility Type",
        "Currency"
    ]
    
    # Ensure all columns exist
    for col in column_order:
        if col not in df.columns:
            df[col] = ""
    
    df = df[column_order]
    
    # Write to Excel
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Invoices', index=False, startrow=5)
        
        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Invoices']
        
        # Add header info (like your example file)
        worksheet['C1'] = 'Batch Date:'
        worksheet['D1'] = date.today().strftime("%d/%m/%Y")
        worksheet['C2'] = 'Batch Name:'
        worksheet['C3'] = 'Compiled by:'
        worksheet['D3'] = 'TEST'
        worksheet['C4'] = 'Tested by:'
        worksheet['D4'] = 'TEST'
        
        # Format header row (row 6, 0-indexed is 5)
        from openpyxl.styles import Font, PatternFill, Alignment
        
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for cell in worksheet[6]:  # Row 6 (1-indexed)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    print(f"✓ Created Excel file: {output_path}")
    print(f"  Total invoices: {len(invoices)}")
    print(f"  File size: {Path(output_path).stat().st_size / 1024:.1f} KB")


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate test Excel file for validation")
    parser.add_argument("--output", default="test_batch.xlsx", help="Output file path")
    parser.add_argument("--count", type=int, default=50, help="Number of invoices to generate")
    args = parser.parse_args()
    
    print("="*70)
    print("GENERATING TEST EXCEL FILE")
    print("="*70)
    
    try:
        # Get units and timelines
        print("\nLoading units and lease data...")
        unit_data = get_units_and_timelines()
        print(f"✓ Found {len(unit_data)} units")
        
        # Generate invoices
        print(f"\nGenerating {args.count} test invoices...")
        invoices = generate_test_invoices(unit_data, args.count)
        print(f"✓ Generated {len(invoices)} invoices")
        
        # Create Excel file
        print(f"\nCreating Excel file...")
        create_excel_file(invoices, args.output)
        
        print("\n" + "="*70)
        print("TEST FILE READY")
        print("="*70)
        print(f"\nYou can now upload this file: {args.output}")
        print("\nExpected validation results:")
        print("  - TEST-OCC-* invoices: Should be Valid (during occupied periods)")
        print("  - TEST-VAC-* invoices: Should be Invalid (during vacancy periods)")
        print("  - TEST-LS-* invoices: Should be 'Landlord Supply - OK TO PAY' (units ending in '00')")
        print("  - TEST-RATE-* invoices: Various determinations based on daily rate")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()




