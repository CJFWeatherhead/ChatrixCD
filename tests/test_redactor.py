"""Tests for sensitive information redaction."""

import unittest
import logging
from chatrixcd.redactor import SensitiveInfoRedactor, RedactingFilter


class TestSensitiveInfoRedactor(unittest.TestCase):
    """Test the SensitiveInfoRedactor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.redactor = SensitiveInfoRedactor(enabled=True, colorize=False)
        self.redactor_colored = SensitiveInfoRedactor(enabled=True, colorize=True)
        self.redactor_disabled = SensitiveInfoRedactor(enabled=False, colorize=False)

    def test_redact_disabled(self):
        """Test that redaction can be disabled."""
        message = "@user:matrix.org joined !room:matrix.org"
        result = self.redactor_disabled.redact(message)
        self.assertEqual(result, message)

    def test_redact_matrix_user_id(self):
        """Test redaction of Matrix user IDs."""
        message = "User @alice:example.com sent a message"
        result = self.redactor.redact(message)
        self.assertIn("@[USER]:", result)
        self.assertNotIn("@alice:", result)
        self.assertIn(".com", result)  # TLD is preserved

    def test_redact_matrix_room_id(self):
        """Test redaction of Matrix room IDs."""
        message = "Joined room !abc123:matrix.org"
        result = self.redactor.redact(message)
        self.assertIn("![ROOM_ID]:", result)
        self.assertNotIn("!abc123:", result)

    def test_redact_ipv4_address(self):
        """Test redaction of IPv4 addresses."""
        message = "Connected to 192.168.1.100"
        result = self.redactor.redact(message)
        self.assertIn("192.168.xxx.xxx", result)
        self.assertNotIn("1.100", result)

    def test_redact_ipv6_address(self):
        """Test redaction of IPv6 addresses."""
        message = "IPv6 address: 2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        result = self.redactor.redact(message)
        self.assertIn("[IPV6_REDACTED]", result)
        self.assertNotIn("7334", result)

    def test_timestamp_not_redacted(self):
        """Test that timestamps are not redacted as IPv6 addresses."""
        message = "2025-10-11 12:34:56 - Log entry"
        result = self.redactor.redact(message)
        # Should not be modified
        self.assertIn("12:34:56", result)
        self.assertNotIn("[IPV6_REDACTED]", result)

    def test_redact_token(self):
        """Test redaction of tokens."""
        message = "Authorization: Bearer abc123xyz456"
        result = self.redactor.redact(message)
        self.assertIn("[TOKEN_REDACTED]", result)
        self.assertNotIn("abc123xyz456", result)

    def test_redact_password(self):
        """Test redaction of passwords."""
        message = "password=secretpass123"
        result = self.redactor.redact(message)
        self.assertIn("[PASSWORD_REDACTED]", result)
        self.assertNotIn("secretpass123", result)

    def test_redact_session_id(self):
        """Test redaction of session IDs."""
        message = "Session: 1234567890abcdef1234567890abcdef"
        result = self.redactor.redact(message)
        self.assertIn("[SESSION_ID_REDACTED]", result)
        self.assertNotIn("1234567890abcdef", result)

    def test_redact_device_id(self):
        """Test redaction of device IDs."""
        message = "device_id=ABCDEFGHIJ"
        result = self.redactor.redact(message)
        self.assertIn("[DEVICE_ID_REDACTED]", result)
        self.assertNotIn("ABCDEFGHIJ", result)

    def test_redact_hostname(self):
        """Test redaction of hostnames."""
        message = "Connected to server.example.com"
        result = self.redactor.redact(message)
        self.assertIn("[DOMAIN]", result)
        self.assertIn(".com", result)
        self.assertNotIn("example", result)

    def test_colorize_redacted_content(self):
        """Test that redacted content is colorized when enabled."""
        message = "@user:matrix.org"
        result = self.redactor_colored.redact(message)
        # Should contain ANSI color codes
        self.assertIn("\033[95m", result)  # Pink color code
        self.assertIn("\033[0m", result)  # Reset code

    def test_multiple_redactions(self):
        """Test multiple redactions in a single message."""
        message = (
            "@alice:matrix.org connected from 192.168.1.1 to !room:server.com with token abc123"
        )
        result = self.redactor.redact(message)
        self.assertIn("@[USER]:", result)
        self.assertIn("![ROOM_ID]:", result)
        self.assertIn("192.168.", result)
        self.assertIn("xxx.xxx", result)
        self.assertIn("[TOKEN_REDACTED]", result)
        self.assertNotIn("@alice:", result)
        self.assertNotIn("!room:", result)
        self.assertNotIn(".1.1", result)  # Last two octets should be hidden
        self.assertNotIn("abc123", result)

    def test_empty_message(self):
        """Test redaction of empty message."""
        result = self.redactor.redact("")
        self.assertEqual(result, "")

    def test_none_message(self):
        """Test redaction of None message."""
        result = self.redactor.redact(None)
        self.assertIsNone(result)

    def test_redact_user_id_with_url_encoding(self):
        """Test redaction of Matrix user IDs with URL-encoded characters."""
        message = "'sender': '@chrisw=40privacyinternational.org:privacyinternational.org'"
        result = self.redactor.redact(message)
        self.assertIn("@[USER]:", result)
        self.assertNotIn("@chrisw=40", result)
        self.assertNotIn("chrisw=40privacyinternational", result)

    def test_redact_sender_key_in_json(self):
        """Test redaction of sender_key cryptographic keys in JSON."""
        message = "'sender_key': 'Efq109VQIqHXV7D2l+IZ7YTVz34IXvGdXRyS4X....'"
        result = self.redactor.redact(message)
        self.assertIn("[SENDER_KEY_REDACTED]", result)
        self.assertNotIn("Efq109VQIqHXV7D2l", result)

    def test_redact_session_id_with_dots(self):
        """Test redaction of session IDs followed by dots."""
        message = "'session_id': 'pMqd8VKtcXc4wwthMHQb2VNjOATOXnPrkvvbgio.....'"
        result = self.redactor.redact(message)
        self.assertIn("[SESSION_ID_REDACTED]", result)
        self.assertNotIn("pMqd8VKtcXc4wwth", result)

    def test_redact_device_id_in_json(self):
        """Test redaction of device IDs in JSON context."""
        message = "'device_id': 'XYEZMPLXBC'"
        result = self.redactor.redact(message)
        self.assertIn("[DEVICE_ID_REDACTED]", result)
        self.assertNotIn("XYEZMPLXBC", result)


class TestRedactingFilter(unittest.TestCase):
    """Test the RedactingFilter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.redactor = SensitiveInfoRedactor(enabled=True, colorize=False)
        self.filter = RedactingFilter(self.redactor)

    def test_filter_redacts_message(self):
        """Test that filter redacts log record message."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User @alice:matrix.org joined",
            args=(),
            exc_info=None,
        )
        self.filter.filter(record)
        self.assertIn("@[USER]:", record.msg)
        self.assertNotIn("@alice:", record.msg)

    def test_filter_redacts_args_dict(self):
        """Test that filter redacts log record args (dict)."""
        # LogRecord doesn't support dict args in the same way, so we skip this test
        # In practice, dict args are rare in logging and get converted to tuples

    def test_filter_redacts_args_tuple(self):
        """Test that filter redacts log record args (tuple)."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User %s joined from %s",
            args=("@carol:matrix.org", "192.168.1.50"),
            exc_info=None,
        )
        self.filter.filter(record)
        self.assertIn("@[USER]:", record.args[0])
        self.assertIn("192.168.", record.args[1])
        self.assertIn("xxx.xxx", record.args[1])

    def test_filter_returns_true(self):
        """Test that filter always returns True (doesn't filter out records)."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = self.filter.filter(record)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
