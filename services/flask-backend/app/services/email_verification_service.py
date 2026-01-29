"""Email verification service for IceCharts."""

import datetime
import logging
import secrets
from typing import Optional

from app.models import get_db
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


def _ensure_utc_aware(dt: datetime.datetime) -> datetime.datetime:
    """Ensure a datetime is timezone-aware (UTC).

    PyDAL+SQLite returns naive datetimes. This normalizes them to
    UTC-aware so comparisons with datetime.now(timezone.utc) work.
    """
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt


class EmailVerificationService:
    """Service for managing email verification."""

    # Token expiration time (24 hours)
    TOKEN_EXPIRATION_HOURS = 24

    @staticmethod
    def create_verification(user_id: int, email: str, user_name: str) -> Optional[str]:
        """
        Create a new email verification record and send verification email.

        Args:
            user_id: User ID to verify
            email: Email address to verify
            user_name: User's name for personalization

        Returns:
            Verification token if successful, None otherwise
        """
        try:
            db = get_db()

            # Generate a secure random token
            token = secrets.token_urlsafe(32)

            # Calculate expiration time
            expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
                hours=EmailVerificationService.TOKEN_EXPIRATION_HOURS
            )

            # Check if there's an existing unverified verification for this user
            existing = db(
                (db.email_verifications.user_id == user_id)
                & (db.email_verifications.is_verified == False)
            ).select().first()

            if existing:
                # Update existing verification
                db(db.email_verifications.id == existing.id).update(
                    verification_token=token,
                    expires_at=expires_at,
                    email=email,
                    created_at=datetime.datetime.now(datetime.timezone.utc),
                )
            else:
                # Create new verification
                db.email_verifications.insert(
                    user_id=user_id,
                    email=email,
                    verification_token=token,
                    expires_at=expires_at,
                    is_verified=False,
                )

            db.commit()

            # Send verification email
            email_sent = EmailService.send_verification_email(email, token, user_name)

            if not email_sent:
                logger.warning(f"Verification created but email failed to send for user {user_id}")

            logger.info(f"Email verification created for user {user_id}")
            return token

        except Exception as e:
            logger.error(f"Failed to create email verification for user {user_id}: {str(e)}")
            db.rollback()
            return None

    @staticmethod
    def verify_email(token: str) -> Optional[dict]:
        """
        Verify an email using the verification token.

        Args:
            token: Verification token

        Returns:
            User dictionary if successful, None otherwise
        """
        try:
            db = get_db()

            # Find verification record
            verification = db(
                (db.email_verifications.verification_token == token)
                & (db.email_verifications.is_verified == False)
            ).select().first()

            if not verification:
                logger.warning(f"Verification token not found or already used: {token[:8]}...")
                return None

            # Check if token has expired
            now = datetime.datetime.now(datetime.timezone.utc)
            expires_at = _ensure_utc_aware(verification.expires_at)
            if expires_at < now:
                logger.warning(f"Verification token expired for user {verification.user_id}")
                return None

            # Mark verification as complete
            db(db.email_verifications.id == verification.id).update(
                is_verified=True,
                verified_at=now,
            )

            # Update user's email_verified status
            db(db.identities.id == verification.user_id).update(
                email_verified=True,
                email_verified_at=now,
            )

            db.commit()

            # Get and return user
            user = db(db.identities.id == verification.user_id).select().first()
            if user:
                user_dict = user.as_dict()
                user_dict.pop("password_hash", None)
                user_dict.pop("mfa_secret", None)
                logger.info(f"Email verified for user {verification.user_id}")
                return user_dict

            return None

        except Exception as e:
            logger.error(f"Failed to verify email with token {token[:8]}...: {str(e)}")
            db.rollback()
            return None

    @staticmethod
    def resend_verification(user_id: int) -> bool:
        """
        Resend verification email to a user.

        Args:
            user_id: User ID

        Returns:
            True if successful, False otherwise
        """
        try:
            db = get_db()

            # Get user
            user = db(db.identities.id == user_id).select().first()
            if not user:
                logger.error(f"User not found: {user_id}")
                return False

            # Check if already verified
            if user.email_verified:
                logger.info(f"User {user_id} email already verified")
                return False

            # Create new verification
            token = EmailVerificationService.create_verification(
                user_id=user_id,
                email=user.email,
                user_name=user.full_name or user.username,
            )

            return token is not None

        except Exception as e:
            logger.error(f"Failed to resend verification for user {user_id}: {str(e)}")
            return False

    @staticmethod
    def get_verification_status(user_id: int) -> dict:
        """
        Get verification status for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with verification status:
            - verified: bool - Whether email is verified
            - pending: bool - Whether there's a pending verification
            - expires_at: datetime - When pending verification expires (if applicable)
        """
        try:
            db = get_db()

            # Get user
            user = db(db.identities.id == user_id).select().first()
            if not user:
                return {"verified": False, "pending": False, "expires_at": None}

            # If already verified, return early
            if user.email_verified:
                return {
                    "verified": True,
                    "pending": False,
                    "expires_at": None,
                    "verified_at": user.email_verified_at,
                }

            # Check for pending verification
            verification = db(
                (db.email_verifications.user_id == user_id)
                & (db.email_verifications.is_verified == False)
            ).select(orderby=~db.email_verifications.created_at).first()

            if verification:
                now = datetime.datetime.now(datetime.timezone.utc)
                is_expired = _ensure_utc_aware(verification.expires_at) < now

                return {
                    "verified": False,
                    "pending": not is_expired,
                    "expires_at": verification.expires_at if not is_expired else None,
                    "expired": is_expired,
                }

            return {"verified": False, "pending": False, "expires_at": None}

        except Exception as e:
            logger.error(f"Failed to get verification status for user {user_id}: {str(e)}")
            return {"verified": False, "pending": False, "expires_at": None}

    @staticmethod
    def cleanup_expired_verifications() -> int:
        """
        Clean up expired verification records.

        Returns:
            Number of records deleted
        """
        try:
            db = get_db()

            # Delete expired, unverified records
            # Note: For SQLite, PyDAL stores naive datetimes, so the
            # DB-level comparison works correctly with naive values.
            now = datetime.datetime.utcnow()
            deleted = db(
                (db.email_verifications.expires_at < now)
                & (db.email_verifications.is_verified == False)
            ).delete()

            db.commit()

            logger.info(f"Cleaned up {deleted} expired verification records")
            return deleted

        except Exception as e:
            logger.error(f"Failed to cleanup expired verifications: {str(e)}")
            db.rollback()
            return 0
