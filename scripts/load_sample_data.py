"""Script to load sample units and leases for testing.

This creates comprehensive sample data to test the validation engine with
various scenarios: active leases, expired leases, gaps between leases,
never-leased units, and landlord supply units.

Usage:
    python scripts/load_sample_data.py [--comprehensive]
    
Options:
    --comprehensive: Create a larger portfolio (20+ units, 30+ leases)
"""

import sys
import argparse
from pathlib import Path
from datetime import date, timedelta
import random

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.models import Unit, Lease


def load_sample_data(comprehensive=False):
    """Load sample units and leases for testing.
    
    Args:
        comprehensive: If True, creates a larger portfolio (20+ units, 30+ leases)
    """
    # Initialize database
    init_db()
    
    with get_session() as session:
        # Check if data already exists
        existing_units = session.query(Unit).count()
        if existing_units > 0:
            print(f"⚠ Found {existing_units} existing unit(s). Skipping sample data load.")
            print("   Use --force to delete existing data and reload.")
            print("   Or delete manually: python scripts/clear_database.py")
            return
        
        print("Loading sample units and leases...\n")
        
        if comprehensive:
            units_data, leases_data = generate_comprehensive_portfolio()
        else:
            units_data, leases_data = generate_basic_portfolio()
        
        # Create units
        units_created = 0
        for unit_data in units_data:
            unit = Unit(**unit_data)
            session.add(unit)
            units_created += 1
            print(f"✓ Created unit: {unit.unit_id}")
        
        session.flush()  # Flush to get IDs
        
        # Create leases
        leases_created = 0
        for lease_data in leases_data:
            lease = Lease(**lease_data)
            session.add(lease)
            leases_created += 1
            print(f"✓ Created lease: {lease.tenant_name} for {lease.unit_id} "
                  f"({lease.lease_start} to {lease.lease_end or 'ongoing'})")
        
        session.commit()
        
        print(f"\n✓ Successfully loaded {units_created} unit(s) and {leases_created} lease(s).")
        print("\nYou can now:")
        print("  1. Generate test Excel: python scripts/generate_test_excel.py")
        print("  2. Upload via web UI: http://localhost:8000/upload")
        print("  3. View results: http://localhost:8000/invoices")


def generate_basic_portfolio():
    """Generate basic portfolio (4 units, 5 leases) for quick testing."""
    today = date.today()
    
    units_data = [
        {
            "unit_id": "SHOP-001",
            "building_name": "High Street Shopping Centre",
            "address_line_1": "123 High Street",
            "city": "London",
            "postcode": "SW1A 1AA"
        },
        {
            "unit_id": "SHOP-002",
            "building_name": "High Street Shopping Centre",
            "address_line_1": "123 High Street",
            "city": "London",
            "postcode": "SW1A 1AA"
        },
        {
            "unit_id": "OFFICE-101",
            "building_name": "Business Park Tower",
            "address_line_1": "456 Business Park",
            "city": "Manchester",
            "postcode": "M1 1AB"
        },
        {
            "unit_id": "SHOP-100",  # Ends in '00' = Landlord Supply
            "building_name": "Retail Complex",
            "address_line_1": "789 Retail Way",
            "city": "Birmingham",
            "postcode": "B1 1CD"
        },
    ]
    
    leases_data = [
        # SHOP-001: Has active lease
        {
            "unit_id": "SHOP-001",
            "tenant_name": "Coffee Shop Ltd",
            "lease_start": today - timedelta(days=365),  # Started 1 year ago
            "lease_end": None  # Ongoing
        },
        # SHOP-002: Had lease, now vacant (gap scenario)
        {
            "unit_id": "SHOP-002",
            "tenant_name": "Bakery Corp",
            "lease_start": today - timedelta(days=730),  # Started 2 years ago
            "lease_end": today - timedelta(days=90)  # Ended 90 days ago
        },
        # SHOP-002: New lease starting soon (gap between leases)
        {
            "unit_id": "SHOP-002",
            "tenant_name": "Tech Store Inc",
            "lease_start": today + timedelta(days=30),  # Starts in 30 days
            "lease_end": None
        },
        # OFFICE-101: Multiple leases with gap
        {
            "unit_id": "OFFICE-101",
            "tenant_name": "Law Firm A",
            "lease_start": today - timedelta(days=1095),  # Started 3 years ago
            "lease_end": today - timedelta(days=180)  # Ended 180 days ago
        },
        {
            "unit_id": "OFFICE-101",
            "tenant_name": "Law Firm B",
            "lease_start": today - timedelta(days=60),  # Started 60 days ago
            "lease_end": None  # Ongoing
        },
        # SHOP-100: No leases (never-leased scenario)
    ]
    
    return units_data, leases_data


def generate_comprehensive_portfolio():
    """Generate comprehensive portfolio (20+ units, 30+ leases) for thorough testing."""
    today = date.today()
    
    # Building names and locations
    buildings = [
        ("High Street Shopping Centre", "123 High Street", "London", "SW1A 1AA"),
        ("Business Park Tower", "456 Business Park", "Manchester", "M1 1AB"),
        ("Retail Complex", "789 Retail Way", "Birmingham", "B1 1CD"),
        ("City Centre Plaza", "321 Main Street", "Leeds", "LS1 1EF"),
        ("Industrial Estate", "654 Factory Road", "Sheffield", "S1 1GH"),
    ]
    
    # Tenant names pool
    tenant_names = [
        "Coffee Shop Ltd", "Bakery Corp", "Tech Store Inc", "Law Firm A", "Law Firm B",
        "Fashion Retail Co", "Electronics Store", "Restaurant Group", "Gym & Fitness Ltd",
        "Pharmacy Chain", "Supermarket Ltd", "Bookstore Inc", "Hardware Store",
        "Beauty Salon", "Dental Practice", "Accountancy Firm", "Insurance Broker",
        "Travel Agency", "Real Estate Agent", "Consulting Group", "Marketing Agency",
        "IT Services Ltd", "Print Shop", "Dry Cleaners", "Hair Salon",
    ]
    
    units_data = []
    leases_data = []
    
    # Generate units across different buildings
    unit_counter = 1
    for building_name, address, city, postcode in buildings:
        # Create 4-5 units per building
        num_units = random.randint(4, 5)
        for i in range(num_units):
            unit_id = f"{building_name.split()[0].upper()}-{unit_counter:03d}"
            
            # Some units end in '00' (Landlord Supply)
            if unit_counter % 5 == 0:
                unit_id = unit_id[:-2] + "00"
            
            units_data.append({
                "unit_id": unit_id,
                "building_name": building_name,
                "address_line_1": address,
                "city": city,
                "postcode": postcode
            })
            
            # Generate leases for this unit (0-3 leases per unit)
            num_leases = random.randint(0, 3)
            
            if num_leases == 0:
                # Never-leased unit (creates ongoing vacancy)
                pass
            else:
                # Generate lease periods
                lease_start_base = today - timedelta(days=random.randint(180, 2000))
                
                for lease_num in range(num_leases):
                    if lease_num == 0:
                        # First lease
                        lease_start = lease_start_base
                    else:
                        # Subsequent leases start after previous one ended
                        prev_lease_end = leases_data[-1]["lease_end"]
                        if prev_lease_end:
                            # Gap between leases (vacancy period)
                            gap_days = random.randint(30, 180)
                            lease_start = prev_lease_end + timedelta(days=gap_days)
                        else:
                            break
                    
                    # Lease duration
                    lease_duration = random.randint(180, 1095)  # 6 months to 3 years
                    lease_end = lease_start + timedelta(days=lease_duration)
                    
                    # Some leases are ongoing
                    if lease_num == num_leases - 1 and random.random() > 0.3:
                        lease_end = None  # Ongoing lease
                    elif lease_end > today:
                        # Future lease
                        if lease_start > today:
                            # Future lease, keep it
                            pass
                        else:
                            # Started in past, ends in future - make it ongoing
                            lease_end = None
                    
                    tenant_name = random.choice(tenant_names)
                    # Ensure unique tenant per unit
                    while any(l["unit_id"] == unit_id and l["tenant_name"] == tenant_name 
                             for l in leases_data):
                        tenant_name = random.choice(tenant_names)
                    
                    leases_data.append({
                        "unit_id": unit_id,
                        "tenant_name": tenant_name,
                        "lease_start": lease_start,
                        "lease_end": lease_end
                    })
            
            unit_counter += 1
    
    return units_data, leases_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load sample units and leases for testing")
    parser.add_argument("--comprehensive", action="store_true", 
                       help="Create comprehensive portfolio (20+ units, 30+ leases)")
    args = parser.parse_args()
    
    try:
        load_sample_data(comprehensive=args.comprehensive)
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)



