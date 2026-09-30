"""Inspect database structure and data.

This script provides a comprehensive view of:
- Database tables and their structure
- Current data counts
- Sample data from each table
- Vacancy/lease timeline visualization
- Validation statistics

Usage:
    python scripts/inspect_database.py [--detailed]
"""

import sys
from pathlib import Path
from datetime import date
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.models import Unit, Lease, Invoice, InvoiceValidation, UnitTimeline, User
from sqlalchemy import func


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def inspect_database(detailed=False):
    """Inspect the database structure and data."""
    init_db()
    
    with get_session() as session:
        # Overview
        print_section("DATABASE OVERVIEW")
        print(f"Units:           {session.query(Unit).count():>6}")
        print(f"Leases:          {session.query(Lease).count():>6}")
        print(f"Invoices:        {session.query(Invoice).count():>6}")
        print(f"Validations:     {session.query(InvoiceValidation).count():>6}")
        print(f"Unit Timelines:  {session.query(UnitTimeline).count():>6}")
        print(f"Users:           {session.query(User).count():>6}")
        
        # Units
        print_section("UNITS")
        units = session.query(Unit).all()
        if units:
            print(f"Total: {len(units)} units\n")
            for unit in units[:10]:
                print(f"  {unit.unit_id:15} | {unit.building_name or 'N/A':30} | {unit.city or 'N/A'}")
            if len(units) > 10:
                print(f"  ... and {len(units) - 10} more units")
        else:
            print("  No units found")
        
        # Leases
        print_section("LEASES")
        leases = session.query(Lease).order_by(Lease.unit_id, Lease.lease_start).all()
        if leases:
            print(f"Total: {len(leases)} leases\n")
            leases_by_unit = defaultdict(list)
            for lease in leases:
                leases_by_unit[lease.unit_id].append(lease)
            
            for unit_id, unit_leases in list(leases_by_unit.items())[:5]:
                print(f"  Unit: {unit_id}")
                for lease in unit_leases:
                    end_str = lease.lease_end.strftime("%Y-%m-%d") if lease.lease_end else "ongoing"
                    print(f"    {lease.tenant_name:25} | {lease.lease_start} to {end_str}")
                print()
            if len(leases_by_unit) > 5:
                print(f"  ... and {len(leases_by_unit) - 5} more units with leases")
        else:
            print("  No leases found")
        
        # Unit Timeline (Vacancy/Occupied periods)
        print_section("UNIT TIMELINE (Vacancy/Occupied Periods)")
        timelines = session.query(UnitTimeline).order_by(UnitTimeline.unit_id, UnitTimeline.period_start).all()
        if timelines:
            print(f"Total: {len(timelines)} timeline periods\n")
            timelines_by_unit = defaultdict(list)
            for timeline in timelines:
                timelines_by_unit[timeline.unit_id].append(timeline)
            
            for unit_id, periods in list(timelines_by_unit.items())[:5]:
                print(f"  Unit: {unit_id}")
                for period in sorted(periods, key=lambda p: p.period_start):
                    end_str = period.period_end.strftime("%Y-%m-%d") if period.period_end else "ongoing"
                    status_icon = "🟢" if period.status == "occupied" else "🔴"
                    days = f" ({period.days_in_period} days)" if period.days_in_period else ""
                    print(f"    {status_icon} {period.status:8} | {period.period_start} to {end_str}{days}")
                print()
            if len(timelines_by_unit) > 5:
                print(f"  ... and {len(timelines_by_unit) - 5} more units with timelines")
        else:
            print("  No timeline data found. Run validation to generate timeline.")
        
        # Invoices
        print_section("INVOICES")
        invoices = session.query(Invoice).order_by(Invoice.created_at.desc()).limit(10).all()
        if invoices:
            total = session.query(Invoice).count()
            print(f"Total: {total} invoices (showing latest 10)\n")
            print(f"{'Invoice #':<15} {'Unit ID':<12} {'Period':<25} {'Amount':>12} {'Batch':<25}")
            print("-" * 90)
            for inv in invoices:
                period = f"{inv.billing_period_start} to {inv.billing_period_end}"
                print(f"{inv.invoice_number:<15} {inv.unit_id:<12} {period:<25} £{inv.gross_amount:>10.2f} {inv.source_batch or 'N/A':<25}")
        else:
            print("  No invoices found")
        
        # Validation Statistics
        print_section("VALIDATION STATISTICS")
        validations = session.query(
            InvoiceValidation.validation_status,
            InvoiceValidation.determination,
            func.count(InvoiceValidation.id).label('count')
        ).group_by(
            InvoiceValidation.validation_status,
            InvoiceValidation.determination
        ).all()
        
        if validations:
            print(f"{'Status':<15} {'Determination':<30} {'Count':>10}")
            print("-" * 60)
            for status, determination, count in validations:
                print(f"{status:<15} {determination:<30} {count:>10}")
            
            # Duplicate stats
            duplicate_count = session.query(InvoiceValidation).filter(
                InvoiceValidation.is_duplicate == 'Yes'
            ).count()
            if duplicate_count > 0:
                print(f"\n  Duplicates detected: {duplicate_count}")
        else:
            print("  No validations found. Run validation to generate results.")
        
        # Batch Statistics
        print_section("BATCH STATISTICS")
        batches = session.query(
            Invoice.source_batch,
            func.count(Invoice.id).label('count')
        ).group_by(Invoice.source_batch).order_by(func.count(Invoice.id).desc()).limit(10).all()
        
        if batches:
            print(f"{'Batch ID':<40} {'Invoice Count':>15}")
            print("-" * 60)
            for batch_id, count in batches:
                print(f"{batch_id or 'N/A':<40} {count:>15}")
        else:
            print("  No batches found")
        
        if detailed:
            # Detailed vacancy analysis
            print_section("DETAILED VACANCY ANALYSIS")
            for unit in session.query(Unit).limit(3).all():
                print(f"\nUnit: {unit.unit_id}")
                leases = session.query(Lease).filter(Lease.unit_id == unit.unit_id).order_by(Lease.lease_start).all()
                timelines = session.query(UnitTimeline).filter(UnitTimeline.unit_id == unit.unit_id).order_by(UnitTimeline.period_start).all()
                
                print("  Leases:")
                for lease in leases:
                    end = lease.lease_end or "ongoing"
                    print(f"    - {lease.tenant_name}: {lease.lease_start} to {end}")
                
                print("  Timeline (derived from leases):")
                for timeline in timelines:
                    end = timeline.period_end or "ongoing"
                    print(f"    - {timeline.status}: {timeline.period_start} to {end}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Inspect database structure and data")
    parser.add_argument("--detailed", action="store_true", help="Show detailed analysis")
    args = parser.parse_args()
    
    try:
        inspect_database(detailed=args.detailed)
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)




