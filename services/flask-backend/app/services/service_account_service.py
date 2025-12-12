"""Service account management service for IceCharts.

This module provides business logic for managing service accounts
and their tokens for external application integration.
"""

import datetime
import secrets
from typing import List, Optional

from app.models import get_db


def generate_client_id() -> str:
    """
    Generate a unique client ID for a service account.

    Returns:
        Client ID in format: sa_xxxxxxxxxxxx
    """
    random_part = secrets.token_hex(12)
    return f"sa_{random_part}"


class ServiceAccountService:
    """Service for managing service accounts and tokens."""

    @staticmethod
    def create_service_account(
        name: str,
        scopes: List[str],
        created_by_id: int,
        description: Optional[str] = None,
        rate_limit: int = 1000,
        tenant_id: int = 1,
    ) -> dict:
        """
        Create a new service account.

        Args:
            name: Name of the service account
            scopes: List of permission scopes
            created_by_id: ID of the user creating the account
            description: Optional description
            rate_limit: Requests per hour limit (default: 1000)
            tenant_id: Tenant ID (default: 1)

        Returns:
            Dictionary containing service account data

        Raises:
            ValueError: If creation fails
        """
        if not name or not name.strip():
            raise ValueError("Service account name cannot be empty")

        if not scopes:
            raise ValueError("At least one scope is required")

        db = get_db()

        try:
            client_id = generate_client_id()

            # Ensure unique client_id
            while db(db.service_accounts.client_id == client_id).count() > 0:
                client_id = generate_client_id()

            account_id = db.service_accounts.insert(
                tenant_id=tenant_id,
                name=name.strip(),
                description=description.strip() if description else None,
                client_id=client_id,
                scopes=scopes,
                rate_limit=rate_limit,
                is_active=True,
                created_by_id=created_by_id,
            )
            db.commit()

            return ServiceAccountService.get_service_account_by_id(account_id)

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to create service account: {str(e)}")

    @staticmethod
    def get_service_account_by_id(account_id: int) -> Optional[dict]:
        """
        Get service account by ID.

        Args:
            account_id: ID of the service account

        Returns:
            Dictionary containing service account data or None if not found
        """
        db = get_db()
        account = db(db.service_accounts.id == account_id).select().first()

        if not account:
            return None

        return ServiceAccountService._serialize_service_account(account)

    @staticmethod
    def get_service_account_by_client_id(client_id: str) -> Optional[dict]:
        """
        Get service account by client ID.

        Args:
            client_id: Client ID of the service account

        Returns:
            Dictionary containing service account data or None if not found
        """
        db = get_db()
        account = db(db.service_accounts.client_id == client_id).select().first()

        if not account:
            return None

        return ServiceAccountService._serialize_service_account(account)

    @staticmethod
    def list_service_accounts(
        tenant_id: int = 1,
        page: int = 1,
        per_page: int = 20,
        include_inactive: bool = False,
    ) -> dict:
        """
        List service accounts for a tenant.

        Args:
            tenant_id: Tenant ID
            page: Page number (1-indexed)
            per_page: Items per page
            include_inactive: Whether to include inactive accounts

        Returns:
            Dictionary with items, total, page, per_page
        """
        db = get_db()

        query = db.service_accounts.tenant_id == tenant_id
        if not include_inactive:
            query &= db.service_accounts.is_active == True

        total = db(query).count()
        offset = (page - 1) * per_page

        accounts = db(query).select(
            orderby=~db.service_accounts.created_at,
            limitby=(offset, offset + per_page),
        )

        return {
            "items": [
                ServiceAccountService._serialize_service_account(a)
                for a in accounts
            ],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def update_service_account(
        account_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        rate_limit: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[dict]:
        """
        Update a service account.

        Args:
            account_id: ID of the service account
            name: New name (optional)
            description: New description (optional)
            scopes: New scopes (optional)
            rate_limit: New rate limit (optional)
            is_active: New active status (optional)

        Returns:
            Updated service account dictionary or None if not found

        Raises:
            ValueError: If update fails
        """
        db = get_db()

        account = db(db.service_accounts.id == account_id).select().first()
        if not account:
            return None

        update_data = {}

        if name is not None:
            if not name.strip():
                raise ValueError("Service account name cannot be empty")
            update_data["name"] = name.strip()

        if description is not None:
            update_data["description"] = description.strip() if description else None

        if scopes is not None:
            if not scopes:
                raise ValueError("At least one scope is required")
            update_data["scopes"] = scopes

        if rate_limit is not None:
            update_data["rate_limit"] = rate_limit

        if is_active is not None:
            update_data["is_active"] = is_active

        if not update_data:
            return ServiceAccountService.get_service_account_by_id(account_id)

        try:
            db(db.service_accounts.id == account_id).update(**update_data)
            db.commit()
            return ServiceAccountService.get_service_account_by_id(account_id)

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to update service account: {str(e)}")

    @staticmethod
    def delete_service_account(account_id: int) -> bool:
        """
        Delete a service account and all its tokens.

        Args:
            account_id: ID of the service account

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If deletion fails
        """
        db = get_db()

        account = db(db.service_accounts.id == account_id).select().first()
        if not account:
            return False

        try:
            # Tokens will be cascade deleted due to FK constraint
            deleted = db(db.service_accounts.id == account_id).delete()
            db.commit()
            return deleted > 0

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to delete service account: {str(e)}")

    @staticmethod
    def generate_token(
        account_id: int,
        name: Optional[str] = None,
        expires_days: int = 365,
    ) -> dict:
        """
        Generate a new token for a service account.

        Args:
            account_id: ID of the service account
            name: Optional name/label for the token
            expires_days: Days until token expires (default: 365)

        Returns:
            Dictionary with 'token' (the JWT) and 'token_info' (token metadata)

        Raises:
            ValueError: If account not found or token generation fails
        """
        from app.auth.jwt_handler import generate_service_token

        db = get_db()

        account = db(db.service_accounts.id == account_id).select().first()
        if not account:
            raise ValueError("Service account not found")

        if not account.is_active:
            raise ValueError("Service account is deactivated")

        try:
            # Generate the JWT token
            sa_dict = account.as_dict()
            token, jti = generate_service_token(sa_dict, expires_days)

            # Store token record in database
            expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=expires_days)

            token_id = db.service_account_tokens.insert(
                service_account_id=account_id,
                token_jti=jti,
                name=name.strip() if name else None,
                expires_at=expires_at,
            )
            db.commit()

            token_record = db.service_account_tokens(token_id)

            return {
                "token": token,
                "token_info": ServiceAccountService._serialize_token(token_record),
            }

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to generate token: {str(e)}")

    @staticmethod
    def list_tokens(account_id: int, include_revoked: bool = False) -> List[dict]:
        """
        List all tokens for a service account.

        Args:
            account_id: ID of the service account
            include_revoked: Whether to include revoked tokens

        Returns:
            List of token dictionaries
        """
        db = get_db()

        query = db.service_account_tokens.service_account_id == account_id
        if not include_revoked:
            query &= db.service_account_tokens.revoked_at == None

        tokens = db(query).select(
            orderby=~db.service_account_tokens.created_at,
        )

        return [ServiceAccountService._serialize_token(t) for t in tokens]

    @staticmethod
    def revoke_token(token_jti: str, revoked_by_id: int) -> bool:
        """
        Revoke a service account token.

        Args:
            token_jti: JTI of the token to revoke
            revoked_by_id: ID of the user revoking the token

        Returns:
            True if revoked, False if not found

        Raises:
            ValueError: If revocation fails
        """
        db = get_db()

        token = db(db.service_account_tokens.token_jti == token_jti).select().first()
        if not token:
            return False

        if token.revoked_at is not None:
            return True  # Already revoked

        try:
            db(db.service_account_tokens.token_jti == token_jti).update(
                revoked_at=datetime.datetime.now(datetime.timezone.utc),
                revoked_by_id=revoked_by_id,
            )
            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to revoke token: {str(e)}")

    @staticmethod
    def revoke_all_tokens(account_id: int, revoked_by_id: int) -> int:
        """
        Revoke all tokens for a service account.

        Args:
            account_id: ID of the service account
            revoked_by_id: ID of the user revoking the tokens

        Returns:
            Number of tokens revoked

        Raises:
            ValueError: If revocation fails
        """
        db = get_db()

        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            updated = db(
                (db.service_account_tokens.service_account_id == account_id) &
                (db.service_account_tokens.revoked_at == None)
            ).update(
                revoked_at=now,
                revoked_by_id=revoked_by_id,
            )
            db.commit()
            return updated

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to revoke tokens: {str(e)}")

    @staticmethod
    def record_token_usage(token_jti: str, ip_address: Optional[str] = None) -> None:
        """
        Record token usage (called by middleware).

        Args:
            token_jti: JTI of the token
            ip_address: IP address of the request
        """
        db = get_db()

        try:
            db(db.service_account_tokens.token_jti == token_jti).update(
                last_used_at=datetime.datetime.now(datetime.timezone.utc),
                last_used_ip=ip_address,
            )
            db.commit()
        except Exception:
            db.rollback()

    @staticmethod
    def _serialize_service_account(account) -> dict:
        """Convert database row to dictionary."""
        return {
            "id": account.id,
            "tenant_id": account.tenant_id,
            "name": account.name,
            "description": account.description,
            "client_id": account.client_id,
            "scopes": account.scopes or [],
            "rate_limit": account.rate_limit,
            "is_active": account.is_active,
            "created_by_id": account.created_by_id,
            "last_used_at": account.last_used_at.isoformat()
            if account.last_used_at else None,
            "created_at": account.created_at.isoformat()
            if account.created_at else None,
            "updated_at": account.updated_at.isoformat()
            if account.updated_at else None,
        }

    @staticmethod
    def _serialize_token(token) -> dict:
        """Convert token database row to dictionary."""
        return {
            "id": token.id,
            "service_account_id": token.service_account_id,
            "token_jti": token.token_jti,
            "name": token.name,
            "expires_at": token.expires_at.isoformat()
            if token.expires_at else None,
            "last_used_at": token.last_used_at.isoformat()
            if token.last_used_at else None,
            "last_used_ip": token.last_used_ip,
            "revoked_at": token.revoked_at.isoformat()
            if token.revoked_at else None,
            "created_at": token.created_at.isoformat()
            if token.created_at else None,
        }
