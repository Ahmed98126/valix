"""Email verification token management."""

import secrets
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models import Base


class EmailVerificationToken(Base):
    """Email verification token for users."""
    
    __tablename__ = "email_verification_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used = Column(Boolean, default=False, nullable=False)  # Boolean: False = not used, True = used
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    user = relationship("User", backref="email_verification_tokens")
    
    @classmethod
    def generate_token(cls) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def create_token(cls, user_id: int, expires_in_hours: int = 48) -> "EmailVerificationToken":
        """Create a new email verification token."""
        token = cls.generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        return cls(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            used=False
        )
    
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)."""
        if self.used:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def mark_as_used(self):
        """Mark token as used."""
        self.used = True
    
    def __repr__(self):
        return f"<EmailVerificationToken(user_id={self.user_id}, expires_at={self.expires_at}, used={self.used})>"

