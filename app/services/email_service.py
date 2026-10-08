import asyncio
import logging

import boto3
from app.configs.env import get_settings
from app.templates.email_templates import (
    render_email_verification_email,
    render_password_reset_email,
)
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.ses_client = boto3.client(
            "ses",
            region_name=self.settings.aws_region,
            aws_access_key_id=self.settings.aws_access_key_id,
            aws_secret_access_key=self.settings.aws_secret_access_key,
        )

    async def send_password_reset_email(
        self,
        *,
        to_email: str,
        reset_link: str,
    ) -> None:
        """
        Send password reset email.
        """
        subject = "Reset your password"
        text_body = (
            "You requested to reset your password.\n\n"
            f"Open this link to continue:\n{reset_link}\n\n"
            "If you did not request this, you can ignore this email."
        )
        html_body = render_password_reset_email(reset_link=reset_link)

        await self._send_email(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )

    async def send_email_verification_email(
        self,
        *,
        to_email: str,
        verification_link: str,
    ) -> None:
        """
        Send email verification email.
        """
        subject = "Verify your email"
        text_body = (
            "Welcome to Blog API.\n\n"
            f"Open this link to verify your email:\n{verification_link}\n\n"
            "If you did not create this account, you can ignore this email."
        )
        html_body = render_email_verification_email(verification_link=verification_link)

        await self._send_email(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )

    async def _send_email(
        self,
        *,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str,
    ) -> None:
        if self.settings.email_provider == "console":
            logger.info(
                "Console email from=%s to=%s subject=%s text=%s",
                self.settings.email_from,
                to_email,
                subject,
                text_body,
            )
            return

        await asyncio.to_thread(
            self._send_email_with_ses,
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )

    def _send_email_with_ses(
        self,
        *,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str,
    ) -> None:
        try:
            response = self.ses_client.send_email(
                Source=self.settings.email_from,
                Destination={
                    "ToAddresses": [to_email],
                },
                Message={
                    "Subject": {
                        "Data": subject,
                        "Charset": "UTF-8",
                    },
                    "Body": {
                        "Text": {
                            "Data": text_body,
                            "Charset": "UTF-8",
                        },
                        "Html": {
                            "Data": html_body,
                            "Charset": "UTF-8",
                        },
                    },
                },
            )
        except ClientError:
            logger.exception("Failed to send email via AWS SES to=%s", to_email)
            raise

        logger.info(
            "Email sent via AWS SES to=%s message_id=%s",
            to_email,
            response.get("MessageId"),
        )

    async def send_two_factor_otp_email(
        self,
        *,
        to_email: str,
        otp: str,
        expires_in_minutes: int,
    ) -> None:
        subject = "Your login verification code"

        text_body = (
            f"Your verification code is: {otp}\n\n"
            f"This code expires in {expires_in_minutes} minutes.\n"
            "If you did not attempt to sign in, change your password."
        )

        html_body = f"""
        <!doctype html>
        <html lang="en">
        <body style="font-family:Arial,sans-serif;color:#202124">
            <h2>Login verification</h2>
            <p>Use this verification code to complete your login:</p>
            <p style="font-size:32px;font-weight:700;letter-spacing:8px">
            {otp}
            </p>
            <p>
            This code expires in {expires_in_minutes} minutes.
            </p>
            <p>
            If you did not attempt to sign in, change your password.
            </p>
        </body>
        </html>
        """

        await self._send_email(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )
