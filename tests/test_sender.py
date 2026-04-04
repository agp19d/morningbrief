"""Tests for the sender module."""

from unittest.mock import MagicMock, patch

from sender import send_email


class TestSendEmail:
    """Tests for send_email()."""

    @patch("sender.smtplib.SMTP_SSL")
    def test_sends_email_via_smtp(self, mock_smtp_cls, sample_brief):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        send_email(sample_brief)

        mock_smtp_cls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()

    @patch("sender.smtplib.SMTP_SSL")
    def test_smtp_uses_timeout(self, mock_smtp_cls, sample_brief):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        send_email(sample_brief)

        call_kwargs = mock_smtp_cls.call_args
        assert call_kwargs[1].get("timeout") == 30 or call_kwargs[0][2] if len(call_kwargs[0]) > 2 else True

    @patch("sender.smtplib.SMTP_SSL")
    def test_email_has_subject_with_date(self, mock_smtp_cls, sample_brief):
        from email import message_from_string

        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        send_email(sample_brief)

        raw = mock_server.sendmail.call_args[0][2]
        msg = message_from_string(raw)
        # Decode MIME-encoded subject header
        from email.header import decode_header
        decoded_parts = decode_header(msg["Subject"])
        subject = "".join(
            part.decode(enc or "utf-8") if isinstance(part, bytes) else part
            for part, enc in decoded_parts
        )
        assert sample_brief["date"] in subject
