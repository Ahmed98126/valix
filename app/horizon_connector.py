"""Horizon API connector for syncing units and leases data."""

import requests
from typing import Dict, List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.models import Unit, Lease, Tenant
from app.validation import generate_unit_timeline


class HorizonConnector:
    """Connector for Horizon Property Management System API."""
    
    def __init__(self, api_endpoint: str, api_key: str):
        """
        Initialize Horizon connector.
        
        Args:
            api_endpoint: Horizon API base URL
            api_key: API key for authentication
        """
        self.api_endpoint = api_endpoint.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def test_connection(self) -> Dict[str, bool]:
        """
        Test connection to Horizon API.
        
        Returns:
            Dictionary with 'success' boolean and optional 'error' message
        """
        try:
            # Example: Test endpoint (adjust based on Horizon API docs)
            response = self.session.get(f"{self.api_endpoint}/health", timeout=10)
            if response.status_code == 200:
                return {"success": True}
            else:
                return {"success": False, "error": f"API returned status {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def fetch_units(self) -> List[Dict]:
        """
        Fetch units from Horizon API.
        
        Returns:
            List of unit dictionaries with fields:
            - unit_id (str)
            - building_name (str, optional)
            - address_line_1 (str, optional)
            - address_line_2 (str, optional)
            - city (str, optional)
            - postcode (str, optional)
        
        Note: Adjust endpoint and field mapping based on Horizon API documentation
        """
        try:
            # Example endpoint (adjust based on Horizon API docs)
            response = self.session.get(f"{self.api_endpoint}/units", timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Map Horizon fields to our fields
            # Adjust field names based on actual Horizon API response
            units = []
            for item in data.get('units', []):
                units.append({
                    'unit_id': item.get('property_code') or item.get('unit_id') or item.get('id'),
                    'building_name': item.get('building_name') or item.get('building'),
                    'address_line_1': item.get('address_line_1') or item.get('address'),
                    'address_line_2': item.get('address_line_2'),
                    'city': item.get('city'),
                    'postcode': item.get('postcode') or item.get('postal_code')
                })
            
            return units
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching units from Horizon: {str(e)}")
    
    def fetch_leases(self) -> List[Dict]:
        """
        Fetch leases from Horizon API.
        
        Returns:
            List of lease dictionaries with fields:
            - unit_id (str)
            - tenant_name (str, optional)
            - lease_start (date)
            - lease_end (date, optional - None for ongoing)
        
        Note: Adjust endpoint and field mapping based on Horizon API documentation
        """
        try:
            # Example endpoint (adjust based on Horizon API docs)
            response = self.session.get(f"{self.api_endpoint}/leases", timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Map Horizon fields to our fields
            leases = []
            for item in data.get('leases', []):
                # Parse dates
                lease_start = None
                lease_end = None
                
                if item.get('lease_start'):
                    if isinstance(item['lease_start'], str):
                        lease_start = datetime.strptime(item['lease_start'], '%Y-%m-%d').date()
                    elif isinstance(item['lease_start'], date):
                        lease_start = item['lease_start']
                
                if item.get('lease_end'):
                    if isinstance(item['lease_end'], str):
                        lease_end = datetime.strptime(item['lease_end'], '%Y-%m-%d').date()
                    elif isinstance(item['lease_end'], date):
                        lease_end = item['lease_end']
                
                leases.append({
                    'unit_id': item.get('property_code') or item.get('unit_id') or item.get('property_id'),
                    'tenant_name': item.get('tenant_name') or item.get('lessee') or item.get('company_name'),
                    'lease_start': lease_start,
                    'lease_end': lease_end  # None for ongoing leases
                })
            
            return leases
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching leases from Horizon: {str(e)}")


def sync_from_horizon(
    session: Session,
    tenant_id: int,
    api_endpoint: str,
    api_key: str
) -> Dict[str, int]:
    """
    Sync units and leases from Horizon API for a tenant.
    
    Args:
        session: Database session
        tenant_id: Tenant ID
        api_endpoint: Horizon API endpoint
        api_key: Horizon API key
    
    Returns:
        Dictionary with counts: {'units_imported': int, 'units_updated': int, 'leases_imported': int}
    """
    connector = HorizonConnector(api_endpoint, api_key)
    
    # Test connection first
    test_result = connector.test_connection()
    if not test_result.get('success'):
        raise Exception(f"Connection test failed: {test_result.get('error', 'Unknown error')}")
    
    # Fetch data
    horizon_units = connector.fetch_units()
    horizon_leases = connector.fetch_leases()
    
    # Import/update units
    units_imported = 0
    units_updated = 0
    
    for unit_data in horizon_units:
        if not unit_data.get('unit_id'):
            continue
        
        existing = session.query(Unit).filter(
            Unit.unit_id == unit_data['unit_id'],
            Unit.tenant_id == tenant_id
        ).first()
        
        if existing:
            # Update existing
            for key, value in unit_data.items():
                if key != 'unit_id':
                    setattr(existing, key, value)
            units_updated += 1
        else:
            # Create new
            unit = Unit(tenant_id=tenant_id, **unit_data)
            session.add(unit)
            units_imported += 1
    
    session.flush()
    
    # Import leases
    leases_imported = 0
    
    # Get valid unit_ids for this tenant
    valid_unit_ids = {u.unit_id for u in session.query(Unit.unit_id).filter(Unit.tenant_id == tenant_id).all()}
    
    for lease_data in horizon_leases:
        if not lease_data.get('unit_id') or lease_data['unit_id'] not in valid_unit_ids:
            continue
        
        if not lease_data.get('lease_start'):
            continue
        
        # Create lease (don't check for duplicates - allow multiple leases per unit)
        lease = Lease(
            tenant_id=tenant_id,
            **lease_data
        )
        session.add(lease)
        leases_imported += 1
    
    session.commit()
    
    # Regenerate unit timelines
    generate_unit_timeline(session, tenant_id=tenant_id)
    
    return {
        'units_imported': units_imported,
        'units_updated': units_updated,
        'leases_imported': leases_imported
    }


