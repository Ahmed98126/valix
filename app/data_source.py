"""Data source integration for external lease/unit data.

This module handles connections to external data sources (APIs, databases, etc.)
where lease and unit data might be stored.
"""

import logging
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from datetime import date
from sqlalchemy.orm import Session

from app.models import Unit, Lease

logger = logging.getLogger(__name__)


class DataSource(ABC):
    """Abstract base class for data sources."""
    
    @abstractmethod
    def get_units(self, tenant_id: int, filters: Optional[Dict] = None) -> List[Dict]:
        """Fetch units from external source."""
        pass
    
    @abstractmethod
    def get_leases(self, tenant_id: int, unit_id: Optional[str] = None, filters: Optional[Dict] = None) -> List[Dict]:
        """Fetch leases from external source."""
        pass
    
    @abstractmethod
    def sync_units(self, session: Session, tenant_id: int) -> int:
        """Sync units from external source to database."""
        pass
    
    @abstractmethod
    def sync_leases(self, session: Session, tenant_id: int, unit_id: Optional[str] = None) -> int:
        """Sync leases from external source to database."""
        pass


class DatabaseDataSource(DataSource):
    """Data source that reads from the application database."""
    
    def get_units(self, tenant_id: int, filters: Optional[Dict] = None) -> List[Dict]:
        """Get units from database."""
        # This is the default - units are already in our database
        return []
    
    def get_leases(self, tenant_id: int, unit_id: Optional[str] = None, filters: Optional[Dict] = None) -> List[Dict]:
        """Get leases from database."""
        return []
    
    def sync_units(self, session: Session, tenant_id: int) -> int:
        """No-op for database source."""
        return 0
    
    def sync_leases(self, session: Session, tenant_id: int, unit_id: Optional[str] = None) -> int:
        """No-op for database source."""
        return 0


class APIDataSource(DataSource):
    """Data source that fetches from external API."""
    
    def __init__(self, api_url: str, api_key: Optional[str] = None, headers: Optional[Dict] = None):
        self.api_url = api_url
        self.api_key = api_key
        self.headers = headers or {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def get_units(self, tenant_id: int, filters: Optional[Dict] = None) -> List[Dict]:
        """Fetch units from API."""
        import requests
        try:
            response = requests.get(
                f"{self.api_url}/units",
                params={"tenant_id": tenant_id, **(filters or {})},
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("units", [])
        except Exception as e:
            logger.error(f"Error fetching units from API: {e}")
            return []
    
    def get_leases(self, tenant_id: int, unit_id: Optional[str] = None, filters: Optional[Dict] = None) -> List[Dict]:
        """Fetch leases from API."""
        import requests
        try:
            params = {"tenant_id": tenant_id, **(filters or {})}
            if unit_id:
                params["unit_id"] = unit_id
            
            response = requests.get(
                f"{self.api_url}/leases",
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("leases", [])
        except Exception as e:
            logger.error(f"Error fetching leases from API: {e}")
            return []
    
    def sync_units(self, session: Session, tenant_id: int) -> int:
        """Sync units from API to database."""
        units_data = self.get_units(tenant_id)
        synced = 0
        
        for unit_data in units_data:
            # Check if unit exists
            existing = session.query(Unit).filter(
                Unit.unit_id == unit_data.get("unit_id"),
                Unit.tenant_id == tenant_id
            ).first()
            
            if existing:
                # Update existing
                existing.building_name = unit_data.get("building_name")
                existing.address_line_1 = unit_data.get("address_line_1")
                existing.address_line_2 = unit_data.get("address_line_2")
                existing.city = unit_data.get("city")
                existing.postcode = unit_data.get("postcode")
            else:
                # Create new
                unit = Unit(
                    tenant_id=tenant_id,
                    unit_id=unit_data.get("unit_id"),
                    building_name=unit_data.get("building_name"),
                    address_line_1=unit_data.get("address_line_1"),
                    address_line_2=unit_data.get("address_line_2"),
                    city=unit_data.get("city"),
                    postcode=unit_data.get("postcode")
                )
                session.add(unit)
            
            synced += 1
        
        session.commit()
        return synced
    
    def sync_leases(self, session: Session, tenant_id: int, unit_id: Optional[str] = None) -> int:
        """Sync leases from API to database."""
        leases_data = self.get_leases(tenant_id, unit_id)
        synced = 0
        
        for lease_data in leases_data:
            # Check if lease exists (by unit_id, tenant_name, lease_start)
            existing = session.query(Lease).filter(
                Lease.unit_id == lease_data.get("unit_id"),
                Lease.tenant_id == tenant_id,
                Lease.lease_start == lease_data.get("lease_start")
            ).first()
            
            if existing:
                # Update existing
                existing.tenant_name = lease_data.get("tenant_name")
                existing.lease_end = lease_data.get("lease_end")
            else:
                # Create new
                lease = Lease(
                    tenant_id=tenant_id,
                    unit_id=lease_data.get("unit_id"),
                    tenant_name=lease_data.get("tenant_name"),
                    lease_start=lease_data.get("lease_start"),
                    lease_end=lease_data.get("lease_end")
                )
                session.add(lease)
            
            synced += 1
        
        session.commit()
        return synced


def get_data_source(tenant_id: int, session: Session) -> DataSource:
    """
    Get the appropriate data source for a tenant.
    
    This checks tenant configuration to determine if they use:
    - Internal database (default)
    - External API
    - Other data sources
    
    Returns:
        DataSource instance
    """
    # TODO: Check tenant configuration for data source settings
    # For now, default to database source
    return DatabaseDataSource()

