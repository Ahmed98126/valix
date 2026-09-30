"""Comprehensive testing workflow for invoice validation system.

This script tests the full workflow:
1. Loads comprehensive sample data (units and leases)
2. Generates multiple test Excel files with various scenarios
3. Provides summary of what to test

Usage:
    python scripts/test_workflow.py [--comprehensive] [--excel-count=3] [--invoices-per-file=50]
"""

import sys
import argparse
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.models import Unit, Lease
from scripts.load_sample_data import load_sample_data
from scripts.generate_test_excel import main as generate_excel


def clear_existing_data():
    """Clear existing units and leases (but keep invoices for testing)."""
    from app.models import Unit, Lease
    
    with get_session() as session:
        lease_count = session.query(Lease).count()
        unit_count = session.query(Unit).count()
        
        if unit_count > 0 or lease_count > 0:
            print(f"\n⚠ Found {unit_count} unit(s) and {lease_count} lease(s).")
            response = input("Delete existing units/leases? (y/N): ").strip().lower()
            
            if response == 'y':
                session.query(Lease).delete()
                session.query(Unit).delete()
                session.commit()
                print("✓ Cleared existing units and leases.")
                return True
            else:
                print("Keeping existing data. Exiting.")
                return False
    return True


def test_workflow(comprehensive=False, excel_count=3, invoices_per_file=50):
    """Run comprehensive testing workflow.
    
    Args:
        comprehensive: Create comprehensive portfolio (20+ units)
        excel_count: Number of test Excel files to generate
        invoices_per_file: Number of invoices per Excel file
    """
    print("="*70)
    print("COMPREHENSIVE TESTING WORKFLOW")
    print("="*70)
    
    # Step 1: Initialize database
    print("\n[1/4] Initializing database...")
    init_db()
    print("✓ Database initialized")
    
    # Step 2: Load sample data
    print(f"\n[2/4] Loading sample data ({'comprehensive' if comprehensive else 'basic'} portfolio)...")
    
    # Check if we should clear existing data
    with get_session() as session:
        existing_units = session.query(Unit).count()
        if existing_units > 0:
            if not clear_existing_data():
                return
    
    # Load sample data
    try:
        load_sample_data(comprehensive=comprehensive)
    except Exception as e:
        print(f"⚠ Error loading sample data: {e}")
        print("   Continuing with existing data...")
    
    # Verify data loaded
    with get_session() as session:
        units = session.query(Unit).count()
        leases = session.query(Lease).count()
        print(f"✓ Loaded {units} unit(s) and {leases} lease(s)")
        
        if units == 0:
            print("ERROR: No units found. Cannot generate test files.")
            return
    
    # Step 3: Generate test Excel files
    print(f"\n[3/4] Generating {excel_count} test Excel file(s)...")
    
    # Import the Excel generator functions directly
    from scripts.generate_test_excel import get_units_and_timelines, generate_test_invoices, create_excel_file
    
    test_files = []
    try:
        # Get units and timelines once
        unit_data = get_units_and_timelines()
        
        for i in range(1, excel_count + 1):
            output_file = f"test_batch_{i:02d}.xlsx"
            print(f"\n  Generating {output_file}...")
            
            # Generate invoices
            invoices = generate_test_invoices(unit_data, invoices_per_file)
            
            # Create Excel file
            create_excel_file(invoices, output_file)
            test_files.append(output_file)
            print(f"  ✓ Created {output_file} ({len(invoices)} invoices)")
            
    except Exception as e:
        print(f"  ⚠ Error generating test files: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 4: Summary
    print("\n" + "="*70)
    print("[4/4] TESTING SUMMARY")
    print("="*70)
    
    print(f"\n✓ Portfolio Data:")
    print(f"  - Units: {units}")
    print(f"  - Leases: {leases}")
    
    print(f"\n✓ Test Files Generated: {len(test_files)}")
    for f in test_files:
        file_path = Path(f)
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"  - {f} ({size_kb:.1f} KB)")
    
    print("\n" + "="*70)
    print("NEXT STEPS - TESTING WORKFLOW")
    print("="*70)
    
    print("\n1. Start the web server:")
    print("   python main.py")
    
    print("\n2. Open the web interface:")
    print("   http://localhost:8000")
    
    print("\n3. Login (or signup if first time)")
    print("   Default: admin@test.com / admin123")
    
    print("\n4. Upload test files:")
    for i, f in enumerate(test_files, 1):
        print(f"   {i}. Upload: {f}")
        print(f"      - Watch progress bar")
        print(f"      - Check for errors/warnings")
        print(f"      - Verify invoice count")
    
    print("\n5. View results:")
    print("   - Dashboard: http://localhost:8000/dashboard")
    print("   - Invoice list: http://localhost:8000/invoices")
    print("   - Use filters: Status, Determination, Batch")
    print("   - Export to CSV")
    
    print("\n6. Verify validation logic:")
    print("   - TEST-OCC-* invoices: Should be 'Invalid' (tenant liable)")
    print("   - TEST-VAC-* invoices: Should be 'Valid' (landlord liable)")
    print("   - TEST-LS-* invoices: Should be 'Landlord Supply - OK TO PAY'")
    print("   - Check daily rate determinations")
    
    print("\n7. Test duplicate detection:")
    print("   - Try uploading the same file twice")
    print("   - Should see duplicate warnings")
    
    print("\n" + "="*70)
    print("TESTING COMPLETE - Ready for validation!")
    print("="*70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive testing workflow for invoice validation system"
    )
    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Create comprehensive portfolio (20+ units, 30+ leases)"
    )
    parser.add_argument(
        "--excel-count",
        type=int,
        default=3,
        help="Number of test Excel files to generate (default: 3)"
    )
    parser.add_argument(
        "--invoices-per-file",
        type=int,
        default=50,
        help="Number of invoices per Excel file (default: 50)"
    )
    
    args = parser.parse_args()
    
    try:
        test_workflow(
            comprehensive=args.comprehensive,
            excel_count=args.excel_count,
            invoices_per_file=args.invoices_per_file
        )
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

