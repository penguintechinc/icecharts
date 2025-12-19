"""Statistics service for admin dashboard metrics."""

import datetime
from collections import defaultdict
from typing import Any, Optional

from app.models import get_db


class StatisticsService:
    """Service for computing system statistics and metrics."""

    @staticmethod
    def get_dashboard_stats(time_range: str = "7d") -> dict[str, Any]:
        """
        Get comprehensive dashboard statistics.

        Time ranges: 1h, 24h, 7d, 30d, 90d, all

        Returns dict with:
        - total_users, active_users (logged in within time_range)
        - total_drawings, drawings_created (within time_range)
        - total_collections, collections_created (within time_range)
        - total_shares, shares_by_type (user/group/public breakdown)
        - shares_by_permission (viewer/editor/admin breakdown)
        - collaboration_sessions_count, active_collaborations
        - email_verification_rate (verified / sent)
        - share_access_count (public share views)
        - database_size_mb (PostgreSQL database size)

        Args:
            time_range: Time range for filtering (1h, 24h, 7d, 30d, 90d, all)

        Returns:
            Dictionary containing all statistics
        """
        time_delta = StatisticsService.parse_time_range(time_range)
        start_time = datetime.datetime.now(datetime.timezone.utc) - time_delta

        db = get_db()

        # User statistics
        total_users = db(db.identities.id > 0).count()
        active_users = db(
            (db.identities.last_login_at != None)
            & (db.identities.last_login_at > start_time)
        ).count()
        new_users = db(db.identities.created_at > start_time).count()
        verified_users = db(db.identities.email_verified == True).count()

        # Drawing statistics
        total_drawings = db(db.drawings.id > 0).count()
        drawings_created = db(db.drawings.created_at > start_time).count()
        public_drawings = db(db.drawings.is_public == True).count()
        template_drawings = db(db.drawings.is_template == True).count()

        # Collection statistics
        total_collections = db(db.collections.id > 0).count()
        collections_created = db(db.collections.created_at > start_time).count()

        # Share statistics
        total_drawing_shares = db(db.drawing_shares.id > 0).count()
        shares_by_type = StatisticsService.get_shares_by_type()
        shares_by_permission = StatisticsService.get_shares_by_permission()

        # Collaboration statistics
        active_collaborations = db(
            (db.collaboration_sessions.is_active == True)
            & (
                db.collaboration_sessions.joined_at
                > datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(minutes=5)
            )
        ).count()
        total_collaboration_sessions = db(
            db.collaboration_sessions.joined_at > start_time
        ).count()

        # Email verification statistics
        email_verifications_sent = db(
            db.email_verifications.created_at > start_time
        ).count()
        email_verifications_completed = db(
            (db.email_verifications.is_verified == True)
            & (db.email_verifications.verified_at != None)
            & (db.email_verifications.verified_at > start_time)
        ).count()

        # Calculate email verification rate (handle division by zero)
        if email_verifications_sent > 0:
            email_verification_rate = (
                email_verifications_completed / email_verifications_sent * 100
            )
        else:
            email_verification_rate = 0.0

        # Share analytics
        share_views = db(db.share_analytics.accessed_at > start_time).count()
        share_views_by_type = StatisticsService.get_share_views_by_type(start_time)

        # System health
        database_size_mb = StatisticsService.get_database_size()

        stats = {
            # User statistics
            "total_users": total_users,
            "active_users": active_users,
            "new_users": new_users,
            "verified_users": verified_users,
            # Drawing statistics
            "total_drawings": total_drawings,
            "drawings_created": drawings_created,
            "public_drawings": public_drawings,
            "template_drawings": template_drawings,
            # Collection statistics
            "total_collections": total_collections,
            "collections_created": collections_created,
            # Share statistics
            "total_drawing_shares": total_drawing_shares,
            "shares_by_type": shares_by_type,
            "shares_by_permission": shares_by_permission,
            # Collaboration statistics
            "active_collaborations": active_collaborations,
            "total_collaboration_sessions": total_collaboration_sessions,
            # Authentication statistics
            "email_verifications_sent": email_verifications_sent,
            "email_verifications_completed": email_verifications_completed,
            "email_verification_rate": round(email_verification_rate, 2),
            # Share analytics
            "share_views": share_views,
            "share_views_by_type": share_views_by_type,
            # System health
            "database_size_mb": database_size_mb,
            # Metadata
            "time_range": time_range,
            "start_time": start_time.isoformat(),
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        return stats

    @staticmethod
    def get_time_series_data(
        metric: str, time_range: str = "7d", interval: str = "1h"
    ) -> list[dict[str, Any]]:
        """
        Get time series data for a specific metric.

        Metrics: users, drawings, collections, shares, collaborations
        Intervals: 5m, 15m, 1h, 6h, 1d

        Args:
            metric: Metric to query (users, drawings, collections, shares, collaborations)
            time_range: Time range for filtering (1h, 24h, 7d, 30d, 90d)
            interval: Interval for data points (5m, 15m, 1h, 6h, 1d)

        Returns:
            List of {timestamp, value} dicts
        """
        time_delta = StatisticsService.parse_time_range(time_range)
        interval_delta = StatisticsService.parse_interval(interval)

        start_time = datetime.datetime.now(datetime.timezone.utc) - time_delta
        db = get_db()

        # Generate time buckets
        data_points = []
        current_time = start_time
        now = datetime.datetime.now(datetime.timezone.utc)

        # Determine the field to query based on metric
        if metric == "users":
            table = db.identities
            date_field = table.created_at
        elif metric == "drawings":
            table = db.drawings
            date_field = table.created_at
        elif metric == "collections":
            table = db.collections
            date_field = table.created_at
        elif metric == "shares":
            table = db.drawing_shares
            date_field = table.created_at
        elif metric == "collaborations":
            table = db.collaboration_sessions
            date_field = table.joined_at
        elif metric == "logins":
            table = db.login_events
            date_field = table.created_at
        else:
            # Unknown metric, return empty list
            return []

        # Generate time series data
        while current_time <= now:
            next_time = current_time + interval_delta

            # Count items created in this time bucket
            count = db((date_field >= current_time) & (date_field < next_time)).count()

            data_points.append({"timestamp": current_time.isoformat(), "value": count})

            current_time = next_time

        return data_points

    @staticmethod
    def get_shares_by_type() -> dict[str, int]:
        """
        Return count of user/group/public shares.

        Returns:
            Dictionary with keys: user, group, public
        """
        db = get_db()

        # Count shares by type
        # User shares: shared_with_id is not null
        user_shares = db(db.drawing_shares.shared_with_id != None).count()

        # Group shares: shared_with_group_id is not null
        group_shares = db(db.drawing_shares.shared_with_group_id != None).count()

        # Public shares: is_public is true
        public_shares = db(db.drawing_shares.is_public == True).count()

        return {
            "user": user_shares,
            "group": group_shares,
            "public": public_shares,
        }

    @staticmethod
    def get_shares_by_permission() -> dict[str, int]:
        """
        Return breakdown of shares by permission level.

        Returns:
            Dictionary with permission levels as keys (viewer, editor, admin)
        """
        db = get_db()

        # Query shares grouped by permission
        result = db(db.drawing_shares.id > 0).select(
            db.drawing_shares.permission,
            db.drawing_shares.id.count(),
            groupby=db.drawing_shares.permission,
        )

        # Convert to dictionary (handle empty database)
        shares_by_permission = {}
        for row in result:
            permission = row.drawing_shares.permission
            count = row._extra[f"COUNT(drawing_shares.id)"]
            shares_by_permission[permission] = count

        # Ensure all permission levels are represented (even if 0)
        for permission in ["viewer", "editor", "admin"]:
            if permission not in shares_by_permission:
                shares_by_permission[permission] = 0

        return shares_by_permission

    @staticmethod
    def get_share_views_by_type(start_time: datetime.datetime) -> dict[str, int]:
        """
        Return share views broken down by type (drawing/collection).

        Args:
            start_time: Start time for filtering analytics

        Returns:
            Dictionary with keys: drawing, collection
        """
        db = get_db()

        # Query share analytics grouped by share_type
        result = db(db.share_analytics.accessed_at > start_time).select(
            db.share_analytics.share_type,
            db.share_analytics.id.count(),
            groupby=db.share_analytics.share_type,
        )

        # Convert to dictionary (handle empty database)
        views_by_type = {}
        for row in result:
            share_type = row.share_analytics.share_type
            count = row._extra[f"COUNT(share_analytics.id)"]
            views_by_type[share_type] = count

        # Ensure both types are represented (even if 0)
        for share_type in ["drawing", "collection"]:
            if share_type not in views_by_type:
                views_by_type[share_type] = 0

        return views_by_type

    @staticmethod
    def get_latency_metrics() -> dict[str, Any]:
        """
        Get API latency metrics from Prometheus.

        Note: This is a placeholder implementation. In a real deployment,
        this would query Prometheus metrics or read from prometheus-flask-exporter.

        Returns:
            Dictionary with latency metrics
        """
        # Placeholder implementation - in production, query Prometheus
        # or use prometheus-flask-exporter registry to get real metrics
        return {
            "avg_response_time_ms": 0.0,
            "p50_response_time_ms": 0.0,
            "p95_response_time_ms": 0.0,
            "p99_response_time_ms": 0.0,
            "requests_per_second": 0.0,
            "error_rate_percent": 0.0,
            "note": "Latency metrics require Prometheus integration. Query /metrics endpoint for raw data.",
        }

    @staticmethod
    def get_top_active_users(limit: int = 10) -> list[dict[str, Any]]:
        """
        Get most active users by drawing count.

        Args:
            limit: Maximum number of users to return (default: 10)

        Returns:
            List of user dicts with drawing counts
        """
        db = get_db()

        # Query users with drawing counts
        result = db(db.drawings.id > 0).select(
            db.identities.id,
            db.identities.username,
            db.identities.email,
            db.identities.full_name,
            db.drawings.id.count(),
            left=db.identities.on(db.identities.id == db.drawings.created_by_id),
            groupby=db.identities.id
            | db.identities.username
            | db.identities.email
            | db.identities.full_name,
            orderby=~db.drawings.id.count(),
            limitby=(0, limit),
        )

        # Convert to list of dicts
        users = []
        for row in result:
            # Skip null users (shouldn't happen, but handle gracefully)
            if not row.identities.id:
                continue

            users.append(
                {
                    "user_id": row.identities.id,
                    "username": row.identities.username,
                    "email": row.identities.email,
                    "full_name": row.identities.full_name or "",
                    "drawing_count": row._extra[f"COUNT(drawings.id)"],
                }
            )

        return users

    @staticmethod
    def get_most_shared_drawings(limit: int = 10) -> list[dict[str, Any]]:
        """
        Get drawings with most shares.

        Args:
            limit: Maximum number of drawings to return (default: 10)

        Returns:
            List of drawing dicts with share counts
        """
        db = get_db()

        # Query drawings with share counts
        result = db(db.drawing_shares.id > 0).select(
            db.drawings.id,
            db.drawings.title,
            db.drawings.created_by_id,
            db.drawing_shares.id.count(),
            left=db.drawings.on(db.drawings.id == db.drawing_shares.drawing_id),
            groupby=db.drawings.id | db.drawings.title | db.drawings.created_by_id,
            orderby=~db.drawing_shares.id.count(),
            limitby=(0, limit),
        )

        # Convert to list of dicts
        drawings = []
        for row in result:
            # Skip null drawings (shouldn't happen, but handle gracefully)
            if not row.drawings.id:
                continue

            drawings.append(
                {
                    "drawing_id": row.drawings.id,
                    "title": row.drawings.title or "Untitled",
                    "owner_id": row.drawings.created_by_id,
                    "share_count": row._extra[f"COUNT(drawing_shares.id)"],
                }
            )

        return drawings

    @staticmethod
    def get_database_size() -> float:
        """
        Get total database size in MB.

        Returns:
            Database size in megabytes (0.0 if not PostgreSQL or query fails)
        """
        db = get_db()

        try:
            # PostgreSQL query for database size
            # This works for PostgreSQL - other databases may need different queries
            result = db.executesql(
                "SELECT pg_database_size(current_database()) as size"
            )

            if result and len(result) > 0:
                size_bytes = result[0][0]
                size_mb = size_bytes / (1024 * 1024)  # Convert to MB
                return round(size_mb, 2)
        except Exception:
            # If query fails (e.g., not PostgreSQL), return 0
            pass

        return 0.0

    @staticmethod
    def parse_time_range(time_range: str) -> datetime.timedelta:
        """
        Parse time range string to timedelta.

        Args:
            time_range: Time range string (1h, 24h, 7d, 30d, 90d, all)

        Returns:
            Corresponding timedelta object
        """
        mapping = {
            "1h": datetime.timedelta(hours=1),
            "24h": datetime.timedelta(hours=24),
            "7d": datetime.timedelta(days=7),
            "30d": datetime.timedelta(days=30),
            "90d": datetime.timedelta(days=90),
            "all": datetime.timedelta(days=365 * 10),  # 10 years
        }
        return mapping.get(time_range, datetime.timedelta(days=7))

    @staticmethod
    def parse_interval(interval: str) -> datetime.timedelta:
        """
        Parse interval string to timedelta.

        Args:
            interval: Interval string (5m, 15m, 1h, 6h, 1d)

        Returns:
            Corresponding timedelta object
        """
        mapping = {
            "5m": datetime.timedelta(minutes=5),
            "15m": datetime.timedelta(minutes=15),
            "1h": datetime.timedelta(hours=1),
            "6h": datetime.timedelta(hours=6),
            "1d": datetime.timedelta(days=1),
        }
        return mapping.get(interval, datetime.timedelta(hours=1))

    @staticmethod
    def get_logins_by_country(
        time_range: str = "7d", limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get login counts grouped by country.

        Args:
            time_range: Time range for filtering (1h, 24h, 7d, 30d, 90d, all)
            limit: Maximum number of countries to return

        Returns:
            List of dicts with country_code, country_name, and login_count
        """
        time_delta = StatisticsService.parse_time_range(time_range)
        start_time = datetime.datetime.now(datetime.timezone.utc) - time_delta

        db = get_db()

        # Query login events grouped by country
        result = db(
            (db.login_events.created_at > start_time)
            & (db.login_events.country_code != None)
            & (db.login_events.success == True)
        ).select(
            db.login_events.country_code,
            db.login_events.country_name,
            db.login_events.id.count(),
            groupby=db.login_events.country_code | db.login_events.country_name,
            orderby=~db.login_events.id.count(),
            limitby=(0, limit),
        )

        # Convert to list of dicts
        countries = []
        for row in result:
            countries.append(
                {
                    "country_code": row.login_events.country_code,
                    "country_name": row.login_events.country_name or "Unknown",
                    "login_count": row._extra.get("COUNT(login_events.id)", 0),
                }
            )

        return countries
