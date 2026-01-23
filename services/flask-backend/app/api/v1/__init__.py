"""API v1 Package - IceCharts REST API Endpoints."""

from flask import Blueprint

# Create API v1 blueprint
api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

# Import collaboration socket handlers (WebSocket events, not a blueprint)
from . import collaboration_socket  # noqa: F401
from .admin import admin_v1_bp
from .admin_license import admin_license_v1_bp
from .admin_settings import admin_settings_v1_bp
from .admin_sso import admin_sso_v1_bp
from .admin_stats import admin_stats_v1_bp

# Import all sub-blueprints
from .auth import auth_v1_bp
from .comments import comments_v1_bp
from .dashboard import dashboard_v1_bp
from .drawings import drawings_v1_bp
from .elder import elder_v1_bp
from .groups import groups_v1_bp
from .health import health_v1_bp
from .libraries import libraries_v1_bp
from .playbook_hooks import playbook_hooks_v1_bp
from .playbooks import playbooks_v1_bp
from .profile import profile_v1_bp
from .service_accounts import service_accounts_v1_bp
from .shares import shares_v1_bp
from .sso import sso_v1_bp
from .storage import storage_v1_bp
from .templates import templates_v1_bp
from .users import users_v1_bp
<<<<<<< HEAD
from .iceruns import iceruns_v1_bp
from .iceruns_executions import iceruns_executions_v1_bp
from .iceruns_hooks import iceruns_hooks_v1_bp
from .iceflows import iceflows_v1_bp
from .iceflows_stages import iceflows_stages_bp
from .iceflows_promotions import iceflows_promotions_bp
from .iceflows_hooks import iceflows_hooks_bp
=======
from .connectors import connectors_v1_bp
>>>>>>> origin/v1.0.X

# Register all blueprints
api_v1_bp.register_blueprint(auth_v1_bp)
api_v1_bp.register_blueprint(profile_v1_bp)
api_v1_bp.register_blueprint(sso_v1_bp)
api_v1_bp.register_blueprint(drawings_v1_bp)
api_v1_bp.register_blueprint(templates_v1_bp)
api_v1_bp.register_blueprint(groups_v1_bp)
api_v1_bp.register_blueprint(elder_v1_bp)
api_v1_bp.register_blueprint(shares_v1_bp)
api_v1_bp.register_blueprint(comments_v1_bp)
api_v1_bp.register_blueprint(libraries_v1_bp)
api_v1_bp.register_blueprint(storage_v1_bp)
api_v1_bp.register_blueprint(admin_v1_bp)
api_v1_bp.register_blueprint(admin_settings_v1_bp)
api_v1_bp.register_blueprint(health_v1_bp)
api_v1_bp.register_blueprint(dashboard_v1_bp)
api_v1_bp.register_blueprint(users_v1_bp)
api_v1_bp.register_blueprint(admin_stats_v1_bp)
api_v1_bp.register_blueprint(admin_sso_v1_bp)
api_v1_bp.register_blueprint(admin_license_v1_bp)
api_v1_bp.register_blueprint(service_accounts_v1_bp)
api_v1_bp.register_blueprint(playbooks_v1_bp)
api_v1_bp.register_blueprint(playbook_hooks_v1_bp)
<<<<<<< HEAD
api_v1_bp.register_blueprint(iceruns_v1_bp)
api_v1_bp.register_blueprint(iceruns_executions_v1_bp)
api_v1_bp.register_blueprint(iceruns_hooks_v1_bp)
api_v1_bp.register_blueprint(iceflows_v1_bp)
api_v1_bp.register_blueprint(iceflows_stages_bp)
api_v1_bp.register_blueprint(iceflows_promotions_bp)
api_v1_bp.register_blueprint(iceflows_hooks_bp)
=======
api_v1_bp.register_blueprint(connectors_v1_bp)
>>>>>>> origin/v1.0.X

__all__ = ["api_v1_bp"]
