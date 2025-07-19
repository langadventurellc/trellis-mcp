---
kind: task
id: T-consolidate-task-management-test
title: Consolidate task management test files
status: open
priority: normal
prerequisites: []
created: '2025-07-18T23:34:36.653730'
updated: '2025-07-18T23:34:36.653730'
schema_version: '1.1'
---
Merge task-related test files that have overlapping functionality: combine test_task_sort_key.py + test_task_sorter.py into test_task_sorting.py, and merge test_complete_task.py + test_complete_task_file_movement.py into test_task_completion.py. Ensure all sorting and completion logic is thoroughly tested.

### Log

