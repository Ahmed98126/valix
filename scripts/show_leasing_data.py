"""Display leasing data (units, leases, and timeline) used for validation.

This shows what data the validation engine uses to determine if invoices
are during occupied or vacant periods.

Usage:
    python scripts/show_leasing_data.py [--unit UNIT_ID]
"""

import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.models import Unit, Lease, UnitTimeline
from app.validation import generate_unit_timeline


def show_leasing_data(unit_id_filter=None):
    """Display all units, leases, and timeline data."""
    init_db()
    
    with get_session() as session:
        # Generate timeline if not exists
        generate_unit_timeline(session)
        
        print("="*80)
        print("LEASING DATA USED FOR VALIDATION")
        print("="*80)
        
        # Get units
        if unit_id_filter:
            units = session.query(Unit).filter(Unit.unit_id == unit_id_filter).all()
            if not units:
                print(f"\n❌ Unit '{unit_id_filter}' not found!")
                return
        else:
            units = session.query(Unit).order_by(Unit.unit_id).all()
        
        print(f"\n📊 TOTAL: {len(units)} Units")
        print("="*80)
        
        for unit in units:
            print(f"\n🏢 UNIT: {unit.unit_id}")
            print(f"   Building: {unit.building_name}")
            print(f"   Address: {unit.address_line_1}, {unit.city} {unit.postcode}")
            
            # Get leases for this unit
            leases = session.query(Lease).filter(
                Lease.unit_id == unit.unit_id
            ).order_by(Lease.lease_start).all()
            
            if leases:
                print(f"\n   📋 LEASES ({len(leases)} total):")
                for i, lease in enumerate(leases, 1):
                    end_date = lease.lease_end.strftime("%Y-%m-%d") if lease.lease_end else "ONGOING"
                    print(f"      {i}. {lease.tenant_name}")
                    print(f"         Period: {lease.lease_start} to {end_date}")
            else:
                print(f"\n   📋 LEASES: None (unit never leased - always vacant)")
            
            # Get timeline for this unit
            timelines = session.query(UnitTimeline).filter(
                UnitTimeline.unit_id == unit.unit_id
            ).order_by(UnitTimeline.period_start).all()
            
            if timelines:
                print(f"\n   📅 TIMELINE ({len(timelines)} periods):")
                for i, timeline in enumerate(timelines, 1):
                    status_icon = "🟢" if timeline.status == "occupied" else "🔴"
                    end_date = timeline.period_end.strftime("%Y-%m-%d") if timeline.period_end else "ONGOING"
                    days = timeline.days_in_period
                    
                    print(f"      {i}. {status_icon} {timeline.status.upper()}: {timeline.period_start} to {end_date} ({days} days)")
                    if timeline.lease_id:
                        lease = session.query(Lease).filter(Lease.id == timeline.lease_id).first()
                        if lease:
                            print(f"         Tenant: {lease.tenant_name}")
            
            print("-" * 80)
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        total_leases = session.query(Lease).count()
        total_timeline_periods = session.query(UnitTimeline).count()
        
        occupied_periods = session.query(UnitTimeline).filter(
            UnitTimeline.status == "occupied"
        ).count()
        vacant_periods = session.query(UnitTimeline).filter(
            UnitTimeline.status == "vacant"
        ).count()
        
        print(f"\n📊 Database Statistics:")
        print(f"   Units: {len(units)}")
        print(f"   Leases: {total_leases}")
        print(f"   Timeline Periods: {total_timeline_periods}")
        print(f"   - Occupied Periods: {occupied_periods}")
        print(f"   - Vacant Periods: {vacant_periods}")
        
        # Show units ending in '00' (Landlord Supply)
        landlord_units = [u for u in units if u.unit_id.endswith('00')]
        if landlord_units:
            print(f"\n🏠 Landlord Supply Units (ending in '00'): {len(landlord_units)}")
            for u in landlord_units:
                print(f"   - {u.unit_id}")
        
        print("\n" + "="*80)
        print("HOW VALIDATION WORKS")
        print("="*80)
        print("""
1. For each invoice, the system checks:
   - Invoice billing period (start date to end date)
   - Overlap with VACANT periods in the timeline
   
2. Status Determination:
   - total_overlap = 0 days → Invalid (no vacancy = tenant liable)
   - total_overlap = invoice_days → Valid (full vacancy = landlord liable)
   - 0 < total_overlap < invoice_days → Needs Review (partial)
   
3. Special Rules:
   - Units ending in '00' → Always "Landlord Supply - OK TO PAY"
   - Daily rate determines final determination for Valid invoices
        """)


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Show leasing data used for validation")
    parser.add_argument("--unit", help="Show data for specific unit ID only")
    args = parser.parse_args()
    
    try:
        show_leasing_data(unit_id_filter=args.unit)
    except Exception as e:
        print(f"\nERROR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


