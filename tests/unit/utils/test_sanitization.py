"""Unit tests for sanitization utilities."""

from src.trellis_mcp.utils.sanitization import sanitize_for_audit


class TestSanitizeForAudit:
    """Test cases for the sanitize_for_audit function."""

    def test_empty_text_returns_empty_marker(self):
        """Test that empty or None text returns [EMPTY] marker."""
        assert sanitize_for_audit("") == "[EMPTY]"
        assert sanitize_for_audit(None) == "[EMPTY]"

    def test_normal_text_passes_through(self):
        """Test that normal, safe text passes through unchanged."""
        safe_texts = [
            "hello world",
            "user-123",
            "normal_file.txt",
            "Project Alpha",
            "Task: implement feature",
            "SUCCESS",
            "error message 404",
        ]

        for text in safe_texts:
            assert sanitize_for_audit(text) == text

    def test_truncation_with_default_length(self):
        """Test that text longer than default max_length (50) gets truncated."""
        long_text = "a" * 60
        result = sanitize_for_audit(long_text)
        assert result == ("a" * 50) + "[TRUNCATED]"

    def test_truncation_with_custom_length(self):
        """Test truncation with custom max_length parameter."""
        text = "hello world this is a long message"
        result = sanitize_for_audit(text, max_length=10)
        assert result == "hello worl[TRUNCATED]"

    def test_text_at_exact_length_boundary(self):
        """Test that text exactly at max_length doesn't get truncated."""
        text = "x" * 50
        result = sanitize_for_audit(text)
        assert result == text
        assert "[TRUNCATED]" not in result

    def test_sql_injection_patterns_redacted(self):
        """Test that SQL injection patterns are detected and redacted."""
        sql_patterns = [
            "DROP TABLE users",
            "select * from passwords",
            "INSERT INTO admin",
            "UPDATE users SET",
            "DELETE FROM logs",
            "UNION SELECT secret",
            "EXEC sp_configure",
        ]

        for pattern in sql_patterns:
            result = sanitize_for_audit(pattern)
            assert result == "[REDACTED]"

    def test_script_injection_patterns_redacted(self):
        """Test that script injection patterns are detected and redacted."""
        script_patterns = [
            "<script>alert('xss')</script>",
            "</script>",
            "javascript:void(0)",
            "vbscript:msgbox",
        ]

        for pattern in script_patterns:
            result = sanitize_for_audit(pattern)
            assert result == "[REDACTED]"

    def test_template_injection_patterns_redacted(self):
        """Test that template injection patterns are detected and redacted."""
        template_patterns = [
            "{{ malicious_code }}",
            "${payload}",
            "#{injection}",
        ]

        for pattern in template_patterns:
            result = sanitize_for_audit(pattern)
            assert result == "[REDACTED]"

    def test_path_traversal_patterns_redacted(self):
        """Test that path traversal patterns are detected and redacted."""
        path_patterns = [
            "../../../etc/passwd",
            "..\\windows\\system32",
            "/etc/shadow",
            "c:\\windows\\system.ini",
            "passwd file access",
            "shadow password",
        ]

        for pattern in path_patterns:
            result = sanitize_for_audit(pattern)
            assert result == "[REDACTED]"

    def test_command_injection_patterns_redacted(self):
        """Test that command injection patterns are detected and redacted."""
        command_patterns = [
            "ls | grep secret",
            "cmd && malicious",
            "command; rm -rf",
            "echo `whoami`",
            "eval $(dangerous)",
        ]

        for pattern in command_patterns:
            result = sanitize_for_audit(pattern)
            assert result == "[REDACTED]"

    def test_sensitive_data_patterns_redacted(self):
        """Test that sensitive data patterns are detected and redacted."""
        sensitive_patterns = [
            "secret key value",
            "password123",
            "api_key_here",
            "auth token",
        ]

        for pattern in sensitive_patterns:
            result = sanitize_for_audit(pattern)
            assert result == "[REDACTED]"

    def test_javascript_patterns_redacted(self):
        """Test that JavaScript patterns are detected and redacted."""
        js_patterns = [
            "function(payload)",
            "eval(malicious)",
            "alert(document.cookie)",
            "null pointer",
            "undefined variable",
        ]

        for pattern in js_patterns:
            result = sanitize_for_audit(pattern)
            assert result == "[REDACTED]"

    def test_case_insensitive_detection(self):
        """Test that pattern detection is case-insensitive."""
        variations = [
            "DROP table",
            "Select * FROM",
            "JavaScript:alert",
            "SECRET_KEY",
            "Password",
        ]

        for pattern in variations:
            result = sanitize_for_audit(pattern)
            assert result == "[REDACTED]"

    def test_partial_matches_trigger_redaction(self):
        """Test that partial matches within larger text trigger redaction."""
        texts_with_embedded_patterns = [
            "Error: select statement failed",
            "File contains <script tag",
            "Found secret in config",
            "Invalid token provided",
        ]

        for text in texts_with_embedded_patterns:
            result = sanitize_for_audit(text)
            assert result == "[REDACTED]"

    def test_safe_words_that_contain_dangerous_substrings(self):
        """Test edge cases where safe words contain dangerous substrings."""
        # These should be redacted because they contain dangerous patterns
        borderline_cases = [
            "selection process",  # contains "select"
            "code with function( call",  # contains "function("
            "insertion sort",  # contains "insert"
            "keyed hash",  # contains "key"
        ]

        for text in borderline_cases:
            result = sanitize_for_audit(text)
            assert result == "[REDACTED]"

    def test_multiple_patterns_in_single_text(self):
        """Test that text with multiple dangerous patterns gets redacted."""
        dangerous_text = "SELECT password FROM users WHERE token = 'secret'"
        result = sanitize_for_audit(dangerous_text)
        assert result == "[REDACTED]"

    def test_redaction_takes_precedence_over_truncation(self):
        """Test that redaction occurs before truncation check."""
        long_dangerous_text = "select " + ("x" * 100)
        result = sanitize_for_audit(long_dangerous_text)
        assert result == "[REDACTED]"
        assert "[TRUNCATED]" not in result

    def test_whitespace_and_special_characters(self):
        """Test handling of whitespace and special characters."""
        safe_special_chars = [
            "user@domain.com",
            "file-name_v2.txt",
            "HTTP/1.1 200 OK",
            "UUID: 12345-67890",
            "(parentheses) and [brackets]",
        ]

        for text in safe_special_chars:
            result = sanitize_for_audit(text)
            assert result == text

    def test_numeric_and_mixed_content(self):
        """Test handling of numeric and mixed alphanumeric content."""
        safe_mixed_content = [
            "123456789",
            "version 2.1.0",
            "error code 404",
            "port 8080",
            "timeout 30s",
        ]

        for text in safe_mixed_content:
            result = sanitize_for_audit(text)
            assert result == text
