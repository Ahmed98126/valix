"""Unit mapping configuration and rules.

This module handles:
- Unit mapping rules (custom mappings per tenant)
- External data source integration
- Batch unit matching
- Mapping confidence scoring
"""

import logging
from typing import List, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Unit, Invoice, Tenant

logger = logging.getLogger(__name__)


class UnitMappingRule:
    """Represents a unit mapping rule."""
    def __init__(
        self,
        source_pattern: str,  # Pattern from invoice (e.g., "2 SAMPLE STREET")
        target_unit_id: str,  # Actual unit_id in database (e.g., "SHOP-001")
        confidence: float = 1.0,  # Confidence score (0.0 to 1.0)
        tenant_id: Optional[int] = None
    ):
        self.source_pattern = source_pattern
        self.target_unit_id = target_unit_id
        self.confidence = confidence
        self.tenant_id = tenant_id


def get_unit_mapping_rules(session: Session, tenant_id: int) -> List[UnitMappingRule]:
    """
    Get unit mapping rules for a tenant.
    
    Rules are stored in Tenant.column_mapping_config as JSON:
    {
        "unit_mappings": [
            {
                "source": "2 SAMPLE STREET",
                "target": "SHOP-001",
                "confidence": 1.0
            }
        ]
    }
    """
    tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant or not tenant.column_mapping_config:
        return []
    
    import json
    try:
        config = json.loads(tenant.column_mapping_config)
        mappings = config.get("unit_mappings", [])
        return [
            UnitMappingRule(
                source_pattern=m["source"],
                target_unit_id=m["target"],
                confidence=m.get("confidence", 1.0),
                tenant_id=tenant_id
            )
            for m in mappings
        ]
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Error parsing unit mapping rules for tenant {tenant_id}: {e}")
        return []


def save_unit_mapping_rule(
    session: Session,
    tenant_id: int,
    source_pattern: str,
    target_unit_id: str,
    confidence: float = 1.0
):
    """Save a unit mapping rule to tenant config."""
    tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return
    
    import json
    from datetime import datetime
    
    # Get existing config
    config = {}
    if tenant.column_mapping_config:
        try:
            config = json.loads(tenant.column_mapping_config)
        except json.JSONDecodeError:
            config = {}
    
    # Initialize unit_mappings if not exists
    if "unit_mappings" not in config:
        config["unit_mappings"] = []
    
    # Check if rule already exists
    existing_rule = None
    for i, rule in enumerate(config["unit_mappings"]):
        if rule.get("source") == source_pattern:
            existing_rule = i
            break
    
    # Update or add rule
    new_rule = {
        "source": source_pattern,
        "target": target_unit_id,
        "confidence": confidence,
        "created_at": datetime.utcnow().isoformat()
    }
    
    if existing_rule is not None:
        config["unit_mappings"][existing_rule] = new_rule
    else:
        config["unit_mappings"].append(new_rule)
    
    # Save back to tenant
    tenant.column_mapping_config = json.dumps(config)
    session.commit()
    
    logger.info(f"Saved unit mapping rule: {source_pattern} -> {target_unit_id} (tenant {tenant_id})")


def apply_mapping_rules(
    session: Session,
    invoice: Invoice,
    tenant_id: int
) -> Optional[str]:
    """
    Apply unit mapping rules to an invoice.
    
    Returns:
        Matched unit_id if rule found, None otherwise
    """
    rules = get_unit_mapping_rules(session, tenant_id)
    
    invoice_unit_id = invoice.unit_id or ""
    invoice_address = invoice.address or ""
    
    # Check exact matches first
    for rule in rules:
        if rule.source_pattern.lower() == invoice_unit_id.lower():
            logger.info(f"Matched invoice {invoice.invoice_number} to unit {rule.target_unit_id} via mapping rule")
            return rule.target_unit_id
        
        # Check if source pattern is in address
        if rule.source_pattern.lower() in invoice_address.lower():
            logger.info(f"Matched invoice {invoice.invoice_number} to unit {rule.target_unit_id} via address mapping rule")
            return rule.target_unit_id
    
    return None

