from datetime import datetime, timezone
from app.extensions import db


class RefreshToken(db.Model):
    """Store refresh tokens in database for revocation"""

    __tablename__ = "refresh_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Track device/session info
    user_agent = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    def __init__(self, user_id, token, expires_at):
        self.user_id = user_id
        self.token = token
        self.expires_at = expires_at

    def is_valid(self):
        """Check if token is valid"""
        return not self.is_revoked and self.expires_at > datetime.now(timezone.utc)

    def revoke(self):
        """Revoke token"""
        self.is_revoked = True
        db.session.commit()

    @staticmethod
    def verify_and_get_user(token):
        """Verify refresh token and return user"""
        refresh_token = RefreshToken.query.filter_by(token=token).first()
        if refresh_token and refresh_token.is_valid():
            return refresh_token.user
        return None
