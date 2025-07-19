---
kind: task
id: T-merge-mixed-task-test-files
title: Remove redundant mixed task test cases
status: open
priority: high
prerequisites: []
created: '2025-07-18T23:34:15.811393'
updated: '2025-07-18T23:39:02.969879'
schema_version: '1.1'
description: Instead of merging the 5 mixed task test files, analyze each file to
  identify and remove redundant test scenarios. Keep the files separate for maintainability
  but eliminate overlapping test logic. Focus on removing duplicate validation, workflow,
  and operation tests while preserving unique edge cases.
---
Consolidate the 5 mixed task test files (test_mixed_dependency_chain_integration.py, test_mixed_task_lifecycle.py, test_mixed_task_operations.py, test_mixed_task_path_resolution.py, test_mixed_task_validation.py) into 2 files: test_mixed_task_core.py and test_mixed_task_integration.py.

### Log

