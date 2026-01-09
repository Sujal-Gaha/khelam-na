import secrets

from app.extensions import db
from datetime import datetime, timedelta, timezone


class OTPCode(db.Model):
    """Store OTP codes for email/SMS verification"""

    __tablename__ = "otp_codes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    email = db.Column(db.String(120), nullable=True, index=True)
    code = db.Column(db.String(10), nullable=False)
    purpose = db.Column(db.String(50), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    attempts = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

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
