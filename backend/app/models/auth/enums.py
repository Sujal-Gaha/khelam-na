import enum


class AuthProviderEnum(enum.Enum):
    """Enum for authentication providers"""

    GOOGLE = "google"
    GITHUB = "github"
    # Won't be adding more than this for now
