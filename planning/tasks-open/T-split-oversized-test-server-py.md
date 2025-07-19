---
kind: task
id: T-split-oversized-test-server-py
title: Split oversized test_server.py file
status: open
priority: high
prerequisites: []
created: '2025-07-18T23:34:04.826800'
updated: '2025-07-18T23:34:04.826800'
schema_version: '1.1'
---
The test_server.py file is 34,229 tokens, making it extremely difficult to maintain. Split this file into logical modules: server core tests, CRUD operation tests, validation tests, and integration workflow tests. Ensure all tests still pass after the split.

### Log

