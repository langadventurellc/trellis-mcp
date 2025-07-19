---
kind: task
id: T-merge-object-management-test
title: Merge object management test files
status: open
priority: low
prerequisites: []
created: '2025-07-18T23:34:53.678751'
updated: '2025-07-18T23:34:53.678751'
schema_version: '1.1'
---
Consolidate object-related test files: merge test_object_parser.py + test_object_roundtrip.py into test_object_operations.py. Review test_object_creation_and_ids.py integration tests for overlap with unit test coverage and remove redundancies while keeping integration-specific test cases.

See `test-inventory.md` for details on existing error handling tests.

### Log

