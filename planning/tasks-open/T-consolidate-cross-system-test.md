---
kind: task
id: T-consolidate-cross-system-test
title: Remove redundant cross-system test duplicates
status: open
priority: high
prerequisites: []
created: '2025-07-18T23:34:10.778183'
updated: '2025-07-18T23:38:57.191654'
schema_version: '1.1'
description: Instead of merging files, identify and remove redundant test cases across
  the 4-5 cross-system test files. Keep the files separate but eliminate overlapping
  test scenarios. Focus on removing duplicate test logic while preserving unique test
  cases and maintaining coverage.
---
Merge the 4-5 cross-system test files into 2 comprehensive files: test_cross_system_prerequisites.py (for prerequisite validation) and test_cross_system_workflows.py (for integration workflows). Remove redundant tests and ensure full coverage is maintained.

### Log

