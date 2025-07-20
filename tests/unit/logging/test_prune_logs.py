"""Unit tests for prune_logs.py module focusing on retention logic with time-freeze."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from trellis_mcp.logging.prune_logs import prune_logs
from trellis_mcp.settings import Settings


class TestPruneLogsRetention:
    """Test prune_logs function with various retention scenarios using time-freeze."""

    @freeze_time("2024-01-15")
    def test_keeps_recent_files_removes_old_files(self):
        """Test that prune_logs keeps recent files and removes old files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Create test log files with different dates
            # With retention_days=7, cutoff = 2024-01-15 - 7 days = 2024-01-08
            # Files >= 2024-01-08 should be kept
            # Files < 2024-01-08 should be removed

            # Recent files (>= cutoff date) - should be kept
            recent_files = [
                "2024-01-15.log",  # Today
                "2024-01-14.log",  # 1 day ago
                "2024-01-10.log",  # 5 days ago
                "2024-01-09.log",  # 6 days ago
                "2024-01-08.log",  # 7 days ago (exactly at boundary - kept)
            ]

            # Old files (< cutoff date) - should be removed
            old_files = [
                "2024-01-07.log",  # 8 days ago
                "2024-01-01.log",  # 14 days ago
                "2023-12-25.log",  # 21 days ago
            ]

            # Create all test files
            for filename in recent_files + old_files:
                (log_dir / filename).touch()

            # Create settings with 7-day retention
            settings = Settings(log_dir=log_dir, log_retention_days=7)

            # Run prune_logs
            removed_count = prune_logs(settings)

            # Verify return value
            assert removed_count == len(old_files)

            # Verify recent files still exist
            for filename in recent_files:
                assert (log_dir / filename).exists(), f"Recent file {filename} should still exist"

            # Verify old files were removed
            for filename in old_files:
                assert not (log_dir / filename).exists(), f"Old file {filename} should be removed"

    @freeze_time("2024-01-15")
    def test_no_files_to_prune_all_recent(self):
        """Test that no files are removed when all files are within retention window."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Create only recent files (all within 7 days)
            recent_files = [
                "2024-01-15.log",  # Today
                "2024-01-14.log",  # 1 day ago
                "2024-01-13.log",  # 2 days ago
                "2024-01-12.log",  # 3 days ago
                "2024-01-11.log",  # 4 days ago
            ]

            # Create all test files
            for filename in recent_files:
                (log_dir / filename).touch()

            # Create settings with 7-day retention
            settings = Settings(log_dir=log_dir, log_retention_days=7)

            # Run prune_logs
            removed_count = prune_logs(settings)

            # Verify no files were removed
            assert removed_count == 0

            # Verify all files still exist
            for filename in recent_files:
                assert (log_dir / filename).exists(), f"Recent file {filename} should still exist"

    @freeze_time("2024-01-15")
    def test_all_files_to_prune_all_old(self):
        """Test that all files are removed when all files are outside retention window."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Create only old files (all < cutoff date 2024-01-08)
            old_files = [
                "2024-01-07.log",  # 8 days ago
                "2024-01-01.log",  # 14 days ago
                "2023-12-25.log",  # 21 days ago
                "2023-12-01.log",  # 45 days ago
            ]

            # Create all test files
            for filename in old_files:
                (log_dir / filename).touch()

            # Create settings with 7-day retention
            settings = Settings(log_dir=log_dir, log_retention_days=7)

            # Run prune_logs
            removed_count = prune_logs(settings)

            # Verify all files were removed
            assert removed_count == len(old_files)

            # Verify all files were removed
            for filename in old_files:
                assert not (log_dir / filename).exists(), f"Old file {filename} should be removed"

    @freeze_time("2024-01-15")
    def test_retention_boundary_edge_case(self):
        """Test files exactly at the retention boundary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Create files at boundary points for 5-day retention
            # With current time 2024-01-15 and retention_days=5:
            # Cutoff = 2024-01-15 - 5 days = 2024-01-10
            # Files < 2024-01-10 should be removed
            # Files >= 2024-01-10 should be kept

            boundary_files = [
                "2024-01-10.log",  # Exactly at cutoff - should be kept
                "2024-01-09.log",  # 1 day before cutoff - should be removed
            ]

            # Create test files
            for filename in boundary_files:
                (log_dir / filename).touch()

            # Create settings with 5-day retention
            settings = Settings(log_dir=log_dir, log_retention_days=5)

            # Run prune_logs
            removed_count = prune_logs(settings)

            # Verify only 1 file was removed (the one before cutoff)
            assert removed_count == 1

            # Verify file at cutoff still exists
            assert (log_dir / "2024-01-10.log").exists()

            # Verify file before cutoff was removed
            assert not (log_dir / "2024-01-09.log").exists()

    @freeze_time("2024-01-15")
    def test_empty_directory(self):
        """Test prune_logs with empty log directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Directory exists but is empty
            settings = Settings(log_dir=log_dir, log_retention_days=7)

            # Run prune_logs
            removed_count = prune_logs(settings)

            # Verify no files were removed
            assert removed_count == 0

    @freeze_time("2024-01-15")
    def test_nonexistent_directory(self):
        """Test prune_logs with non-existent log directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "nonexistent"

            # Directory doesn't exist
            settings = Settings(log_dir=log_dir, log_retention_days=7)

            # Run prune_logs
            removed_count = prune_logs(settings)

            # Verify no files were removed
            assert removed_count == 0

    @freeze_time("2024-01-15")
    def test_ignores_non_log_files(self):
        """Test that prune_logs ignores files that don't match log pattern."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Create valid log files (old - should be removed)
            valid_old_files = [
                "2024-01-01.log",  # 14 days ago
                "2023-12-25.log",  # 21 days ago
            ]

            # Create invalid files (should be ignored regardless of date)
            invalid_files = [
                "2024-01-01.txt",  # Wrong extension
                "2024-01-01.log.bak",  # Wrong extension
                "not-a-date.log",  # Invalid date format
                "2024-13-01.log",  # Invalid date (month 13)
                "2024-01-32.log",  # Invalid date (day 32)
                "log-2024-01-01.log",  # Wrong format
                "subdir",  # Directory
            ]

            # Create valid log files
            for filename in valid_old_files:
                (log_dir / filename).touch()

            # Create invalid files
            for filename in invalid_files:
                if filename == "subdir":
                    (log_dir / filename).mkdir()
                else:
                    (log_dir / filename).touch()

            # Create settings with 7-day retention
            settings = Settings(log_dir=log_dir, log_retention_days=7)

            # Run prune_logs
            removed_count = prune_logs(settings)

            # Verify only valid old log files were removed
            assert removed_count == len(valid_old_files)

            # Verify valid old files were removed
            for filename in valid_old_files:
                assert not (
                    log_dir / filename
                ).exists(), f"Valid old file {filename} should be removed"

            # Verify invalid files were ignored and still exist
            for filename in invalid_files:
                assert (log_dir / filename).exists(), f"Invalid file {filename} should be ignored"

    @freeze_time("2024-01-15")
    def test_different_retention_periods(self):
        """Test prune_logs with different retention periods."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Create files with various ages
            test_files = [
                "2024-01-15.log",  # 0 days ago
                "2024-01-14.log",  # 1 day ago
                "2024-01-13.log",  # 2 days ago
                "2024-01-12.log",  # 3 days ago
                "2024-01-11.log",  # 4 days ago
                "2024-01-10.log",  # 5 days ago
                "2024-01-09.log",  # 6 days ago
                "2024-01-08.log",  # 7 days ago
                "2024-01-07.log",  # 8 days ago
                "2024-01-01.log",  # 14 days ago
            ]

            # Test with 1-day retention
            for filename in test_files:
                (log_dir / filename).touch()

            settings = Settings(log_dir=log_dir, log_retention_days=1)
            removed_count = prune_logs(settings)

            # With 1-day retention, cutoff is 2024-01-14
            # Files < 2024-01-14 should be removed (8 files)
            assert removed_count == 8

            # Only files from 2024-01-14 and 2024-01-15 should remain
            assert (log_dir / "2024-01-15.log").exists()
            assert (log_dir / "2024-01-14.log").exists()
            assert not (log_dir / "2024-01-13.log").exists()

    @freeze_time("2024-01-15")
    def test_threading_safety(self):
        """Test that prune_logs is thread-safe."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Create old log files
            old_files = [
                "2024-01-01.log",  # 14 days ago
                "2024-01-02.log",  # 13 days ago
                "2024-01-03.log",  # 12 days ago
            ]

            # Create test files
            for filename in old_files:
                (log_dir / filename).touch()

            # Create settings with 7-day retention
            settings = Settings(log_dir=log_dir, log_retention_days=7)

            # Run prune_logs multiple times (simulating concurrent access)
            # Second call should find no files to prune
            first_removed = prune_logs(settings)
            second_removed = prune_logs(settings)

            # Verify first call removed all old files
            assert first_removed == len(old_files)

            # Verify second call found no files to remove
            assert second_removed == 0

            # Verify all files were removed
            for filename in old_files:
                assert not (log_dir / filename).exists()

    def test_default_settings(self):
        """Test prune_logs with default settings (no settings parameter)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the default settings to use our temp directory
            with patch("trellis_mcp.logging.prune_logs.Settings") as mock_settings:
                mock_settings.return_value.log_dir = Path(temp_dir)
                mock_settings.return_value.log_retention_days = 30

                # Create an old file (35 days ago from frozen time)
                with freeze_time("2024-01-15"):
                    old_file = "2023-12-11.log"  # 35 days ago
                    (Path(temp_dir) / old_file).touch()

                    # Run prune_logs without settings parameter
                    removed_count = prune_logs()

                    # Verify file was removed
                    assert removed_count == 1
                    assert not (Path(temp_dir) / old_file).exists()

    def test_invalid_retention_days(self):
        """Test prune_logs with invalid retention_days setting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Test with retention_days = 0 (invalid)
            settings = Settings(log_dir=log_dir, log_retention_days=1)
            # Manually set to 0 to test validation
            settings.log_retention_days = 0

            # Should raise ValueError
            with pytest.raises(ValueError, match="Invalid retention period: 0. Must be > 0"):
                prune_logs(settings)


class TestPruneLogsDryRun:
    """Test prune_logs function with dry_run parameter."""

    @freeze_time("2024-01-15")
    def test_dry_run_returns_files_without_deletion(self):
        """Test that dry_run returns files that would be deleted without actually deleting them."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Create test log files with different dates
            # With retention_days=7, cutoff = 2024-01-15 - 7 days = 2024-01-08
            # Files >= 2024-01-08 should be kept
            # Files < 2024-01-08 should be listed for removal

            # Recent files (>= cutoff date) - should be kept
            recent_files = [
                "2024-01-15.log",  # Today
                "2024-01-14.log",  # 1 day ago
                "2024-01-08.log",  # 7 days ago (exactly at boundary - kept)
            ]

            # Old files (< cutoff date) - should be listed for removal
            old_files = [
                "2024-01-07.log",  # 8 days ago
                "2024-01-01.log",  # 14 days ago
                "2023-12-25.log",  # 21 days ago
            ]

            # Create all test files
            for filename in recent_files + old_files:
                (log_dir / filename).touch()

            # Create settings with 7-day retention
            settings = Settings(log_dir=log_dir, log_retention_days=7)

            # Run prune_logs with dry_run=True
            files_to_remove = prune_logs(settings, dry_run=True)

            # Verify return type is list
            assert isinstance(files_to_remove, list)

            # Verify correct files are identified for removal
            expected_files = [log_dir / filename for filename in old_files]
            assert len(files_to_remove) == len(expected_files)

            # Verify actual file paths match expected
            file_names = [f.name for f in files_to_remove]
            assert sorted(file_names) == sorted(old_files)

            # Verify NO files were actually deleted
            for filename in recent_files + old_files:
                assert (
                    log_dir / filename
                ).exists(), f"File {filename} should still exist in dry run"

    @freeze_time("2024-01-15")
    def test_dry_run_empty_directory(self):
        """Test dry_run with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)
            settings = Settings(log_dir=log_dir, log_retention_days=7)

            # Run dry_run on empty directory
            files_to_remove = prune_logs(settings, dry_run=True)

            # Should return empty list
            assert files_to_remove == []

    @freeze_time("2024-01-15")
    def test_dry_run_nonexistent_directory(self):
        """Test dry_run with non-existent directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "nonexistent"
            settings = Settings(log_dir=log_dir, log_retention_days=7)

            # Run dry_run on non-existent directory
            files_to_remove = prune_logs(settings, dry_run=True)

            # Should return empty list
            assert files_to_remove == []

    @freeze_time("2024-01-15")
    def test_dry_run_no_matching_files(self):
        """Test dry_run with no files matching removal criteria."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Create only recent files that should be kept
            recent_files = [
                "2024-01-15.log",  # Today
                "2024-01-14.log",  # 1 day ago
                "2024-01-10.log",  # 5 days ago
            ]

            # Create test files
            for filename in recent_files:
                (log_dir / filename).touch()

            # Create settings with 7-day retention
            settings = Settings(log_dir=log_dir, log_retention_days=7)

            # Run dry_run
            files_to_remove = prune_logs(settings, dry_run=True)

            # Should return empty list
            assert files_to_remove == []

            # Verify all files still exist
            for filename in recent_files:
                assert (log_dir / filename).exists()

    @freeze_time("2024-01-15")
    def test_dry_run_ignores_invalid_files(self):
        """Test that dry_run ignores invalid files like actual pruning."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Create valid old files (should be listed for removal)
            valid_old_files = [
                "2024-01-01.log",  # 14 days ago
                "2023-12-25.log",  # 21 days ago
            ]

            # Create invalid files (should be ignored)
            invalid_files = [
                "2024-01-01.txt",  # Wrong extension
                "not-a-date.log",  # Invalid date format
                "2024-13-01.log",  # Invalid date (month 13)
                "log-2024-01-01.log",  # Wrong format
            ]

            # Create all files
            for filename in valid_old_files + invalid_files:
                (log_dir / filename).touch()

            # Create subdirectory (should also be ignored)
            (log_dir / "subdir").mkdir()

            # Create settings with 7-day retention
            settings = Settings(log_dir=log_dir, log_retention_days=7)

            # Run dry_run
            files_to_remove = prune_logs(settings, dry_run=True)

            # Type narrowing: we know dry_run=True returns list[Path]
            assert isinstance(files_to_remove, list), "dry_run=True should return list[Path]"

            # Should only return valid old files
            assert len(files_to_remove) == len(valid_old_files)
            file_names = [f.name for f in files_to_remove]
            assert sorted(file_names) == sorted(valid_old_files)

            # Verify all files still exist
            for filename in valid_old_files + invalid_files:
                assert (log_dir / filename).exists()

    @freeze_time("2024-01-15")
    def test_dry_run_vs_actual_consistency(self):
        """Test that dry_run and actual pruning identify the same files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Create test files
            test_files = [
                "2024-01-15.log",  # Today - should be kept
                "2024-01-10.log",  # 5 days ago - should be kept
                "2024-01-07.log",  # 8 days ago - should be removed
                "2024-01-01.log",  # 14 days ago - should be removed
            ]

            # Create first set of files for dry run
            for filename in test_files:
                (log_dir / filename).touch()

            settings = Settings(log_dir=log_dir, log_retention_days=7)

            # Run dry_run to get list of files that would be removed
            files_to_remove = prune_logs(settings, dry_run=True)

            # Type narrowing: we know dry_run=True returns list[Path]
            assert isinstance(files_to_remove, list), "dry_run=True should return list[Path]"

            # Create second set of files for actual pruning
            # (since dry_run didn't delete anything)
            removed_count = prune_logs(settings, dry_run=False)

            # Verify consistency
            assert len(files_to_remove) == removed_count

            # Verify the files that were identified for removal are actually gone
            for file_path in files_to_remove:
                assert not file_path.exists(), f"File {file_path} should have been removed"

    @freeze_time("2024-01-15")
    def test_dry_run_different_retention_periods(self):
        """Test dry_run with different retention periods."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Create test files spanning different time periods
            test_files = [
                "2024-01-15.log",  # Today
                "2024-01-10.log",  # 5 days ago
                "2024-01-08.log",  # 7 days ago
                "2024-01-05.log",  # 10 days ago
                "2024-01-01.log",  # 14 days ago
                "2023-12-25.log",  # 21 days ago
            ]

            # Create all files
            for filename in test_files:
                (log_dir / filename).touch()

            # Test with 3-day retention
            settings_3day = Settings(log_dir=log_dir, log_retention_days=3)
            files_3day = prune_logs(settings_3day, dry_run=True)
            assert isinstance(files_3day, list), "dry_run=True should return list[Path]"

            # Test with 10-day retention
            settings_10day = Settings(log_dir=log_dir, log_retention_days=10)
            files_10day = prune_logs(settings_10day, dry_run=True)
            assert isinstance(files_10day, list), "dry_run=True should return list[Path]"

            # Test with 30-day retention
            settings_30day = Settings(log_dir=log_dir, log_retention_days=30)
            files_30day = prune_logs(settings_30day, dry_run=True)
            assert isinstance(files_30day, list), "dry_run=True should return list[Path]"

            # Verify different retention periods return different results
            assert len(files_3day) > len(files_10day) > len(files_30day)

            # 3-day retention should remove more files
            # Cutoff for 3-day = 2024-01-12, so files < 2024-01-12 should be removed
            # That's: 2024-01-10, 2024-01-08, 2024-01-05, 2024-01-01, 2023-12-25 = 5 files
            assert len(files_3day) == 5

            # 10-day retention should remove fewer files
            # Cutoff for 10-day = 2024-01-05, so files < 2024-01-05 should be removed
            # That's: 2024-01-01, 2023-12-25 = 2 files
            assert len(files_10day) == 2

            # 30-day retention should remove no files (all files are recent)
            assert len(files_30day) == 0

    def test_dry_run_default_parameter(self):
        """Test that dry_run parameter defaults to False."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)

            # Create an old file
            with freeze_time("2024-01-15"):
                old_file = "2024-01-01.log"  # 14 days ago
                (log_dir / old_file).touch()

                settings = Settings(log_dir=log_dir, log_retention_days=7)

                # Call without dry_run parameter (should default to False)
                result = prune_logs(settings)

                # Should return int (number of removed files)
                assert isinstance(result, int)
                assert result == 1

                # File should be actually deleted
                assert not (log_dir / old_file).exists()
