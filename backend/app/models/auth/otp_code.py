import secrets
from typing import Optional

from app.extensions import db
from datetime import datetime, timedelta, timezone

from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class OTPCode(db.Model):
    """Store OTP codes for email/SMS verification"""

    __tablename__ = "otp_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    expires_at: Mapped[datetime]  = mapped_column(DateTime, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))

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

    def is_valid(self):
        """Check if OTP is valid"""
        return (
            not self.is_used
            and self.expires_at > datetime.now(timezone.utc)
            and self.attempts < 5
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
    def create_and_send(purpose, email=None, user_id=None):
        """Create OTP and send via email/SMS"""
        # Clean up old unused OTPs
        if email:
            OTPCode.query.filter_by(
                email=email, purpose=purpose, is_used=False
            ).delete()

        otp = OTPCode(purpose=purpose, email=email, user_id=user_id)
        db.session.add(otp)
        db.session.commit()

        # Send OTP
        if email:
            print(f"OTP stolen {otp}")
            pass

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
