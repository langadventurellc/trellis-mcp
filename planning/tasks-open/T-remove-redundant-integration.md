---
kind: task
id: T-remove-redundant-integration
title: Remove redundant integration tests
status: open
priority: low
prerequisites: []
created: '2025-07-18T23:34:58.981543'
updated: '2025-07-18T23:34:58.981543'
schema_version: '1.1'
---
Review integration tests that duplicate unit test coverage and remove redundancies. Focus on test_integration_task_lifecycle_workflow.py vs individual unit tests, test_dependency_management.py vs test_dependency_resolver.py, and test_integration_schema_loading.py vs loader unit tests. Keep only tests that add integration-specific value.

See `test-inventory.md` for details on existing error handling tests.

### Log

