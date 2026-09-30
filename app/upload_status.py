"""Track upload status and errors for user feedback."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.models import Base

class UploadStatus(Base):
    """Track file upload processing status."""
    
    __tablename__ = "upload_status"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    batch_id = Column(String, nullable=False, index=True)
    file_name = Column(String, nullable=False)
    status = Column(String, nullable=False)  # 'processing', 'completed', 'error'
    total_rows = Column(Integer, nullable=True)
    invoices_created = Column(Integer, default=0, nullable=False)
    errors = Column(Text, nullable=True)  # JSON string of errors
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    user_id = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<UploadStatus(tenant_id={self.tenant_id}, batch_id='{self.batch_id}', status='{self.status}')>"



