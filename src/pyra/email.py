"""Email sending adapters for Pyra.

Pyra does not bundle an email provider — you pick one.
This module provides a Protocol and two built-in implementations:
  - ConsoleEmailSender  — prints to stdout (development default)
  - SMTPEmailSender     — sends via any SMTP server (production)

Usage with AuthManager::

    from pyra.email import SMTPEmailSender, send_magic_link

    sender = SMTPEmailSender(
        host=os.environ["SMTP_HOST"],
        port=465,
        username=os.environ["SMTP_USER"],
        password=os.environ["SMTP_PASS"],
        from_address="no-reply@myapp.com",
        use_ssl=True,
    )

    # In your login page:
    token = auth.create_magic_link_token(email)
    send_magic_link(
        sender,
        to=email,
        token=token,
        base_url="https://myapp.com",
        app_name="My App",
    )
"""
from __future__ import annotations

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Protocol, runtime_checkable


@runtime_checkable
class EmailSender(Protocol):
    """Protocol for email senders. Implement this to plug in any provider."""

    def send(self, to: str, subject: str, body_text: str, body_html: str = "") -> None:
        """Send an email.

        Args:
            to: Recipient email address.
            subject: Email subject line.
            body_text: Plain-text body (always required — spam filters prefer it).
            body_html: Optional HTML body. If provided, sends a multipart message.
        """
        ...


class ConsoleEmailSender:
    """Development sender — prints emails to stdout instead of sending them.

    This is the default. Replace with SMTPEmailSender in production.
    """

    def send(self, to: str, subject: str, body_text: str, body_html: str = "") -> None:
        print(f"\n{'='*60}")
        print(f"[pyra email] To: {to}")
        print(f"[pyra email] Subject: {subject}")
        print(f"[pyra email] Body:\n{body_text}")
        print(f"{'='*60}\n")


class SMTPEmailSender:
    """Production email sender via SMTP.

    Compatible with any SMTP provider: Gmail, Mailgun, SendGrid, Postmark, Resend, etc.

    Args:
        host: SMTP server hostname.
        port: SMTP port (465 for SSL, 587 for STARTTLS, 25 for plain).
        username: SMTP authentication username.
        password: SMTP authentication password.
        from_address: The From address for outgoing email.
        use_ssl: Use SMTP_SSL (port 465). Mutually exclusive with use_tls.
        use_tls: Use STARTTLS (port 587).
        timeout: Connection timeout in seconds.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_address: str,
        use_ssl: bool = False,
        use_tls: bool = True,
        timeout: int = 10,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_address = from_address
        self.use_ssl = use_ssl
        self.use_tls = use_tls
        self.timeout = timeout

    def send(self, to: str, subject: str, body_text: str, body_html: str = "") -> None:
        msg = self._build_message(to, subject, body_text, body_html)
        if self.use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=self.timeout) as server:
                server.login(self.username, self.password)
                server.sendmail(self.from_address, to, msg.as_string())
        else:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as server:
                if self.use_tls:
                    server.starttls(context=ssl.create_default_context())
                server.login(self.username, self.password)
                server.sendmail(self.from_address, to, msg.as_string())

    def _build_message(self, to: str, subject: str, body_text: str, body_html: str) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_address
        msg["To"] = to
        msg.attach(MIMEText(body_text, "plain"))
        if body_html:
            msg.attach(MIMEText(body_html, "html"))
        return msg


def send_magic_link(
    sender: EmailSender,
    to: str,
    token: str,
    base_url: str,
    app_name: str = "Pyra App",
    next_url: str = "/",
    subject: str = "",
) -> None:
    """Send a magic-link login email.

    Args:
        sender: Any EmailSender implementation.
        to: Recipient email address.
        token: Magic-link token from AuthManager.create_magic_link_token().
        base_url: Your app's public URL (e.g. "https://myapp.com").
        app_name: Display name shown in the email.
        next_url: Where to redirect after successful login.
        subject: Override default subject line.
    """
    verify_url = f"{base_url.rstrip('/')}/auth/verify?token={token}&next={next_url}"
    subj = subject or f"Your {app_name} login link"
    body_text = (
        f"Click the link below to log in to {app_name}.\n\n"
        f"{verify_url}\n\n"
        f"This link expires in 15 minutes and can only be used once.\n"
        f"If you didn't request this, you can ignore this email.\n"
    )
    body_html = f"""<!doctype html>
<html><body style="font-family:-apple-system,sans-serif;max-width:480px;margin:2rem auto;color:#111;">
<h2 style="font-size:1.25rem;">Log in to {app_name}</h2>
<p>Click the button below to log in. This link expires in 15 minutes.</p>
<a href="{verify_url}" style="display:inline-block;padding:0.6rem 1.4rem;background:#6366f1;
color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">Log in</a>
<p style="margin-top:1.5rem;font-size:0.8rem;color:#6b7280;">
Or copy this URL: {verify_url}<br>
If you didn't request this, ignore this email.
</p>
</body></html>"""
    sender.send(to=to, subject=subj, body_text=body_text, body_html=body_html)
