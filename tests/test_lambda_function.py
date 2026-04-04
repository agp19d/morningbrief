"""Tests for the Lambda handler."""

import json
from unittest.mock import patch

from lambda_function import lambda_handler


class TestLambdaHandler:
    """Tests for lambda_handler()."""

    @patch("lambda_function.send_email")
    @patch("lambda_function.fetch_brief")
    @patch("lambda_function.validate_runtime_config")
    def test_success_returns_200(self, mock_validate, mock_fetch, mock_send, sample_brief):
        mock_fetch.return_value = sample_brief

        result = lambda_handler({}, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "sent"
        assert body["headline"] == sample_brief["headline"]

    @patch("lambda_function.send_email")
    @patch("lambda_function.fetch_brief")
    @patch("lambda_function.validate_runtime_config")
    def test_calls_pipeline_in_order(self, mock_validate, mock_fetch, mock_send, sample_brief):
        mock_fetch.return_value = sample_brief

        lambda_handler({}, None)

        mock_validate.assert_called_once()
        mock_fetch.assert_called_once()
        mock_send.assert_called_once_with(sample_brief)

    @patch("lambda_function.validate_runtime_config", side_effect=Exception("boom"))
    def test_error_returns_500(self, mock_validate):
        result = lambda_handler({}, None)

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert body["status"] == "error"

    @patch("lambda_function.send_email", side_effect=Exception("SMTP failed"))
    @patch("lambda_function.fetch_brief")
    @patch("lambda_function.validate_runtime_config")
    def test_send_failure_returns_500(self, mock_validate, mock_fetch, mock_send, sample_brief):
        mock_fetch.return_value = sample_brief

        result = lambda_handler({}, None)

        assert result["statusCode"] == 500
