"""Tests for email module."""
from __future__ import annotations

from pyra.email import ConsoleEmailSender, SMTPEmailSender, EmailSender, send_magic_link


def test_console_sender_is_email_sender():
    assert isinstance(ConsoleEmailSender(), EmailSender)


def test_smtp_sender_is_email_sender():
    s = SMTPEmailSender("smtp.example.com", 587, "u", "p", "no-reply@example.com")
    assert isinstance(s, EmailSender)


def test_console_sender_prints(capsys):
    sender = ConsoleEmailSender()
    sender.send("user@example.com", "Hello", "body text")
    captured = capsys.readouterr()
    assert "user@example.com" in captured.out
    assert "Hello" in captured.out
    assert "body text" in captured.out


def test_send_magic_link_calls_sender():
    calls = []

    class CaptureSender:
        def send(self, to, subject, body_text, body_html=""):
            calls.append({"to": to, "subject": subject, "body": body_text})

    send_magic_link(
        CaptureSender(),
        to="alice@example.com",
        token="tok123",
        base_url="https://myapp.com",
        app_name="TestApp",
        next_url="/dashboard",
    )
    assert len(calls) == 1
    assert calls[0]["to"] == "alice@example.com"
    assert "tok123" in calls[0]["body"]
    assert "https://myapp.com/auth/verify" in calls[0]["body"]


def test_send_magic_link_includes_next_url():
    bodies = []

    class CaptureSender:
        def send(self, to, subject, body_text, body_html=""):
            bodies.append(body_text)

    send_magic_link(
        CaptureSender(),
        to="x@x.com",
        token="abc",
        base_url="https://app.com",
        next_url="/profile",
    )
    assert "next=/profile" in bodies[0]


def test_smtp_sender_builds_message():
    s = SMTPEmailSender("h", 587, "u", "p", "from@x.com")
    msg = s._build_message("to@x.com", "Sub", "plain", "<b>html</b>")
    assert msg["Subject"] == "Sub"
    assert msg["To"] == "to@x.com"
    assert msg["From"] == "from@x.com"
