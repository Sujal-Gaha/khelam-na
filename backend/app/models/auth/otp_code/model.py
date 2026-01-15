import secrets
import uuid

from typing import Optional

from app.extensions import db
from datetime import datetime, timedelta, timezone

from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column


class OTPCode(db.Model):
    """Store OTP codes for email/SMS verification"""

    __tablename__ = "otp_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __init__(
        self,
        purpose,
        email=None,
        user_id=None,
        code_length=6,
        expires_in=600,
    ):
        self.user_id = user_id
        self.email = email
        self.purpose = purpose
        self.code = "".join([str(secrets.randbelow(10)) for _ in range(code_length)])
        self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    def _utc(self, dt: datetime) -> datetime:
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    def is_valid(self):
        """Check if OTP is valid"""
        now = datetime.now(timezone.utc)

        return (
            not self.is_used and self._utc(self.expires_at) > now and self.attempts < 5
        )

    def verify(self, code):
        """Verify OTP code"""
        self.attempts += 1

        if not self.is_valid():
            db.session.commit()
            return False

        if self.code == code:
            self.is_used = True
            db.session.commit()
            return True

        db.session.commit()
        return False

    @staticmethod
    def create_and_send(purpose, email, user_id=None):
        """Create OTP and send via email/SMS"""
        OTPCode.query.filter_by(email=email, purpose=purpose, is_used=False).delete()

        otp = OTPCode(purpose=purpose, email=email, user_id=user_id, code_length=8)
        db.session.add(otp)
        db.session.commit()

        print(f"OTP stolen {otp.code}")

        return otp

    @staticmethod
    def verify_code(code, purpose, email=None):
        """Verify OTP code"""
        query = OTPCode.query.filter_by(purpose=purpose, is_used=False)

        if email:
            query = query.filter_by(email=email)

        else:
            return False

        otp = query.order_by(OTPCode.created_at.desc()).first()

        if otp and otp.verify(code):
            return True
        return False
