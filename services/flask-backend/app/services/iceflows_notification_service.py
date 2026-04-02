"""IceFlows notification service with support for email, Slack, and webhook channels."""

import hashlib
import hmac
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class IceFlowsNotificationService:
    """Service for sending notifications through multiple channels for IceFlows pipelines."""

    # Event to template mapping
    EVENT_TEMPLATES = {
        "promotion_requested": {
            "subject": "Promotion Requested: {pipeline_name}",
            "title": "New Promotion Awaiting Approval",
            "color": "#0099FF",
            "emoji": "📋",
        },
        "promotion_approved": {
            "subject": "Promotion Approved: {pipeline_name}",
            "title": "Promotion Approved",
            "color": "#00AA00",
            "emoji": "✅",
        },
        "promotion_rejected": {
            "subject": "Promotion Rejected: {pipeline_name}",
            "title": "Promotion Rejected",
            "color": "#FF3333",
            "emoji": "❌",
        },
        "promotion_override": {
            "subject": "Day Restriction Overridden: {pipeline_name}",
            "title": "Day Restriction Overridden",
            "color": "#FF9900",
            "emoji": "⚠️",
        },
        "execution_started": {
            "subject": "Pipeline Execution Started: {pipeline_name}",
            "title": "Pipeline Execution Started",
            "color": "#0099FF",
            "emoji": "▶️",
        },
        "execution_completed": {
            "subject": "Pipeline Execution Completed: {pipeline_name}",
            "title": "Pipeline Execution Completed",
            "color": "#00AA00",
            "emoji": "✅",
        },
        "execution_failed": {
            "subject": "Pipeline Execution Failed: {pipeline_name}",
            "title": "Pipeline Execution Failed",
            "color": "#FF3333",
            "emoji": "❌",
        },
    }

    # Max retries for webhook delivery
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 2  # exponential backoff: 1s, 2s, 4s

    @staticmethod
    def send_notification(
        flow_id: int, event_type: str, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Send notification through all configured channels for a flow.

        Args:
            flow_id: IceFlows flow ID
            event_type: Type of event (promotion_requested, execution_completed, etc.)
            data: Event data containing pipeline_name, stage_name, error, etc.

        Returns:
            List of result dictionaries with channel, status, and error info
        """
        results = []

        try:
            # Import here to avoid circular dependency
            from app.models import get_db

            db = get_db()

            # Get all enabled notification channels for this flow
            query = db(db.iceflows_notifications.flow_id == flow_id) & (
                db.iceflows_notifications.is_enabled == True
            )
            notifications = query.select()

            if not notifications:
                logger.debug(f"No enabled notifications configured for flow {flow_id}")
                return results

            # Get notification template
            subject, body = IceFlowsNotificationService._get_notification_template(
                event_type, data
            )

            # Send to each configured channel
            for notification in notifications:
                try:
                    config = notification.config or {}

                    # Check if this event type is in the notification's event list
                    events = notification.events or []
                    if event_type not in events:
                        logger.debug(
                            f"Event {event_type} not in notification {notification.notification_id} event list"
                        )
                        continue

                    channel_type = notification.channel_type

                    if channel_type == "email":
                        result = IceFlowsNotificationService._send_email_notification(
                            config, event_type, data, subject, body
                        )
                    elif channel_type == "slack":
                        result = IceFlowsNotificationService._send_slack_notification(
                            config, event_type, data, subject, body
                        )
                    elif channel_type == "webhook":
                        result = IceFlowsNotificationService._send_webhook_notification(
                            config, event_type, data, subject, body
                        )
                    else:
                        result = {
                            "channel": channel_type,
                            "status": "failed",
                            "error": f"Unknown channel type: {channel_type}",
                        }

                    # Log the notification
                    IceFlowsNotificationService._log_notification(
                        db,
                        notification.id,  # Use DB id for foreign key reference
                        flow_id,
                        event_type,
                        channel_type,
                        config.get(
                            "recipient",
                            config.get("email", config.get("webhook_url", "")),
                        ),
                        subject,
                        body,
                        result.get("status", "failed"),
                        result.get("error", ""),
                    )

                    results.append(result)

                except Exception as e:
                    logger.error(
                        f"Error sending notification for flow {flow_id}, event {event_type}: {str(e)}"
                    )
                    results.append(
                        {
                            "channel": notification.channel_type,
                            "status": "failed",
                            "error": str(e),
                        }
                    )

        except Exception as e:
            logger.error(f"Error processing notifications for flow {flow_id}: {str(e)}")

        return results

    @staticmethod
    def _send_email_notification(
        config: Dict[str, Any],
        event_type: str,
        data: Dict[str, Any],
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        """
        Send email notification.

        Args:
            config: Email configuration with 'email' field
            event_type: Type of event
            data: Event data
            subject: Email subject
            body: Email body text

        Returns:
            Result dictionary with status and optional error
        """
        try:
            email = config.get("email")
            if not email:
                return {
                    "channel": "email",
                    "status": "failed",
                    "error": "No email configured",
                }

            # Generate HTML body
            template = IceFlowsNotificationService.EVENT_TEMPLATES.get(event_type, {})
            emoji = template.get("emoji", "📧")
            title = template.get("title", "Notification")

            body_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: {template.get('color', '#4F46E5')}; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
                    .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
                    .info {{ background-color: #f0f0f0; padding: 15px; border-left: 4px solid {template.get('color', '#4F46E5')}; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{emoji} {title}</h1>
                    </div>
                    <div class="content">
                        <p>{body}</p>
                        <div class="info">
                            <strong>Pipeline:</strong> {data.get('pipeline_name', 'N/A')}<br>
                            <strong>Stage:</strong> {data.get('stage_name', 'N/A')}<br>
                            <strong>Timestamp:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
                        </div>
                    </div>
                    <div class="footer">
                        <p>This is an automated notification from IceFlows.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            success = EmailService.send_email(
                to=email,
                subject=subject,
                body_html=body_html,
                body_text=body,
            )

            if success:
                logger.info(f"Email notification sent to {email}")
                return {"channel": "email", "status": "sent", "recipient": email}
            else:
                return {
                    "channel": "email",
                    "status": "failed",
                    "error": "EmailService returned False",
                }

        except Exception as e:
            logger.error(f"Email notification failed: {str(e)}")
            return {"channel": "email", "status": "failed", "error": str(e)}

    @staticmethod
    def _send_slack_notification(
        config: Dict[str, Any],
        event_type: str,
        data: Dict[str, Any],
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        """
        Send Slack notification via webhook with rich block formatting.

        Args:
            config: Slack configuration with 'webhook_url' field
            event_type: Type of event
            data: Event data
            subject: Notification subject
            body: Notification body

        Returns:
            Result dictionary with status and optional error
        """
        try:
            webhook_url = config.get("webhook_url")
            if not webhook_url:
                return {
                    "channel": "slack",
                    "status": "failed",
                    "error": "No webhook URL configured",
                }

            template = IceFlowsNotificationService.EVENT_TEMPLATES.get(event_type, {})
            color = template.get("color", "#808080")
            emoji = template.get("emoji", "📧")
            title = template.get("title", "Notification")

            # Build Slack message with blocks
            message = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": f"{emoji} {title}"},
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Pipeline:*\n{data.get('pipeline_name', 'N/A')}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Stage:*\n{data.get('stage_name', 'N/A')}",
                            },
                        ],
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*Details:*\n{body}"},
                    },
                ],
                "attachments": [
                    {
                        "fallback": subject,
                        "color": color,
                        "footer": "IceFlows Notification",
                        "ts": int(time.time()),
                    }
                ],
            }

            # Add error details if present
            if data.get("error"):
                message["blocks"].insert(
                    4,
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Error:*\n```{data.get('error')}```",
                        },
                    },
                )

            response = requests.post(webhook_url, json=message, timeout=10)

            if response.status_code == 200:
                logger.info(f"Slack notification sent to {webhook_url}")
                return {"channel": "slack", "status": "sent", "webhook": webhook_url}
            else:
                return {
                    "channel": "slack",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}",
                }

        except Exception as e:
            logger.error(f"Slack notification failed: {str(e)}")
            return {"channel": "slack", "status": "failed", "error": str(e)}

    @staticmethod
    def _send_webhook_notification(
        config: Dict[str, Any],
        event_type: str,
        data: Dict[str, Any],
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        """
        Send generic webhook notification with retry logic and HMAC signature support.

        Args:
            config: Webhook configuration with 'webhook_url' and optional 'secret' field
            event_type: Type of event
            data: Event data
            subject: Notification subject
            body: Notification body

        Returns:
            Result dictionary with status and optional error
        """
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            return {
                "channel": "webhook",
                "status": "failed",
                "error": "No webhook URL configured",
            }

        secret = config.get("secret")
        headers = config.get("headers", {}) or {}
        headers["Content-Type"] = "application/json"

        # Build payload
        payload = {
            "event_type": event_type,
            "subject": subject,
            "body": body,
            "pipeline_name": data.get("pipeline_name"),
            "stage_name": data.get("stage_name"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

        # Add HMAC signature if secret is configured
        if secret:
            payload_json = __import__("json").dumps(payload, sort_keys=True)
            signature = hmac.new(
                secret.encode(), payload_json.encode(), hashlib.sha256
            ).hexdigest()
            headers["X-IceFlows-Signature"] = f"sha256={signature}"

        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(IceFlowsNotificationService.MAX_RETRIES):
            try:
                response = requests.post(
                    webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=10,
                )

                if response.status_code in (200, 201, 202):
                    logger.info(
                        f"Webhook notification sent to {webhook_url} (attempt {attempt + 1})"
                    )
                    return {
                        "channel": "webhook",
                        "status": "sent",
                        "webhook": webhook_url,
                        "attempts": attempt + 1,
                    }
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"

                    # Don't retry on 4xx errors (client errors)
                    if 400 <= response.status_code < 500:
                        return {
                            "channel": "webhook",
                            "status": "failed",
                            "error": last_error,
                        }

            except requests.exceptions.Timeout:
                last_error = "Request timeout"
            except requests.exceptions.ConnectionError:
                last_error = "Connection error"
            except Exception as e:
                last_error = str(e)

            # Wait before retry with exponential backoff
            if attempt < IceFlowsNotificationService.MAX_RETRIES - 1:
                wait_time = IceFlowsNotificationService.RETRY_BACKOFF_FACTOR**attempt
                logger.warning(
                    f"Webhook send attempt {attempt + 1} failed: {last_error}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)

        logger.error(
            f"Webhook notification failed after {IceFlowsNotificationService.MAX_RETRIES} attempts: {last_error}"
        )
        return {
            "channel": "webhook",
            "status": "failed",
            "error": f"Failed after {IceFlowsNotificationService.MAX_RETRIES} attempts: {last_error}",
            "attempts": IceFlowsNotificationService.MAX_RETRIES,
        }

    @staticmethod
    def _get_notification_template(
        event_type: str, data: Dict[str, Any]
    ) -> tuple[str, str]:
        """
        Get notification template for event type.

        Args:
            event_type: Type of event
            data: Event data for template substitution

        Returns:
            Tuple of (subject, body)
        """
        template = IceFlowsNotificationService.EVENT_TEMPLATES.get(
            event_type,
            {
                "subject": "IceFlows Notification: {pipeline_name}",
                "title": "Notification",
            },
        )

        # Format subject with data
        subject = template.get("subject", "IceFlows Notification").format(
            **{k: v for k, v in data.items() if isinstance(v, (str, int, float))}
        )

        # Generate body based on event type
        pipeline_name = data.get("pipeline_name", "Unknown")
        stage_name = data.get("stage_name", "N/A")
        error = data.get("error", "")

        if event_type == "promotion_requested":
            body = f"A new promotion has been requested for {pipeline_name} at stage {stage_name}."
        elif event_type == "promotion_approved":
            body = f"Promotion approved for {pipeline_name} at stage {stage_name}."
        elif event_type == "promotion_rejected":
            reason = data.get("reason", "No reason provided")
            body = f"Promotion rejected for {pipeline_name} at stage {stage_name}. Reason: {reason}"
        elif event_type == "promotion_override":
            body = f"Day restriction override applied for {pipeline_name} at stage {stage_name}."
        elif event_type == "execution_started":
            body = f"Pipeline execution started for {pipeline_name}."
        elif event_type == "execution_completed":
            body = f"Pipeline execution completed successfully for {pipeline_name}."
        elif event_type == "execution_failed":
            body = f"Pipeline execution failed for {pipeline_name}. Error: {error}"
        else:
            body = f"IceFlows event: {event_type} for {pipeline_name}"

        return subject, body

    @staticmethod
    def _log_notification(
        db: Any,
        notification_id: str,
        flow_id: int,
        event_type: str,
        channel_type: str,
        recipient: str,
        subject: str,
        body: str,
        status: str,
        error_message: str = "",
    ) -> None:
        """
        Log notification to iceflows_notification_log table.

        Args:
            db: PyDAL database instance
            notification_id: ID of the notification configuration
            flow_id: Flow ID
            event_type: Type of event
            channel_type: Channel type (email, slack, webhook)
            recipient: Recipient address/URL
            subject: Notification subject
            body: Notification body
            status: Send status (sent, failed, pending)
            error_message: Error message if failed
        """
        try:
            db.iceflows_notification_log.insert(
                log_id=str(uuid.uuid4()),
                notification_id=notification_id,
                flow_id=flow_id,
                event_type=event_type,
                channel_type=channel_type,
                recipient=recipient,
                subject=subject,
                body=body,
                status=status,
                error_message=error_message if error_message else None,
                sent_at=(datetime.now(timezone.utc) if status == "sent" else None),
            )
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}")
