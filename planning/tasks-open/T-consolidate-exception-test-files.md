---
kind: task
id: T-consolidate-exception-test-files
title: Consolidate exception test files
status: open
priority: normal
prerequisites: []
created: '2025-07-18T23:34:25.965225'
updated: '2025-07-18T23:34:25.965225'
schema_version: '1.1'
---
Merge the 8 granular exception test files in tests/unit/exceptions/ into 3 logical files: test_validation_exceptions.py (validation errors), test_task_workflow_exceptions.py (task-specific errors), and test_system_exceptions.py (system-level errors). Maintain all test coverage.

### Log

