"""Tests for the signed transport layer."""
import pytest

from pyra.transport import (
    Session,
    new_session,
    sign_outbound,
    verify_inbound,
)


def test_sign_and_verify_roundtrip():
    s_server = new_session()
    # Simulate the client by reusing the same secret (in production the
    # client gets its own key via the auth handshake).
    s_client = Session(session_id=s_server.session_id, secret=s_server.secret)

    msg = sign_outbound(s_server, {"hello": "world"})
    payload = verify_inbound(s_client, msg)
    assert payload == {"hello": "world"}


def test_replay_rejected():
    s_server = new_session()
    s_client = Session(session_id=s_server.session_id, secret=s_server.secret)

    msg = sign_outbound(s_server, {"x": 1})
    verify_inbound(s_client, msg)
    with pytest.raises(ValueError, match="replay"):
        verify_inbound(s_client, msg)


def test_tampered_signature_rejected():
    s_server = new_session()
    s_client = Session(session_id=s_server.session_id, secret=s_server.secret)
    msg = sign_outbound(s_server, {"x": 1})
    msg["sig"] = "deadbeef" * 8
    with pytest.raises(ValueError, match="invalid signature"):
        verify_inbound(s_client, msg)


def test_tampered_payload_rejected():
    s_server = new_session()
    s_client = Session(session_id=s_server.session_id, secret=s_server.secret)
    msg = sign_outbound(s_server, {"x": 1})
    msg["payload"] = {"x": 2}  # tamper after signing
    with pytest.raises(ValueError, match="invalid signature"):
        verify_inbound(s_client, msg)


def test_wrong_secret_rejected():
    s_server = new_session()
    s_other = new_session()  # different secret
    msg = sign_outbound(s_server, {"x": 1})
    with pytest.raises(ValueError, match="invalid signature"):
        verify_inbound(s_other, msg)


def test_msg_id_monotonic():
    s = new_session()
    m1 = sign_outbound(s, {})
    m2 = sign_outbound(s, {})
    m3 = sign_outbound(s, {})
    assert m1["msg_id"] == 1
    assert m2["msg_id"] == 2
    assert m3["msg_id"] == 3
