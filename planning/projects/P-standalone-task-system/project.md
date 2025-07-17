---
kind: project
id: P-standalone-task-system
title: Standalone Task System Implementation
status: in-progress
priority: normal
prerequisites: []
created: '2025-07-17T18:07:16.015653'
updated: '2025-07-17T18:07:16.015653'
schema_version: '1.0'
---
### Executive Summary
Implement a standalone task system that allows users to create tasks without the overhead of creating projects, epics, or features. This system will provide a simplified workflow for small, independent work items while maintaining full integration with existing Trellis MCP functionality.

### Functional Requirements

**Core Functionality:**
- Create standalone tasks with no parent requirement
- Support standard task status workflow: `open` → `in-progress` → `review` → `done`
- Enable prerequisite relationships between standalone tasks and existing hierarchy-based tasks
- Integrate with existing MCP tools: `listBacklog()`, `claimNextTask()`, `completeTask()`
- Support standard task priorities: `high`, `normal`, `low`

**File System Structure:**
- Store standalone tasks in `planning/tasks/T-{task-id}.md` 
- Maintain YAML front-matter structure consistent with hierarchy-based tasks
- Support both `tasks-open` and `tasks-done` organizational patterns

**Cross-System Integration:**
- Enable prerequisites between standalone tasks and hierarchy-based tasks (projects/epics/features)
- Ensure cycle detection works across both standalone and hierarchy-based systems
- Maintain consistent prerequisite validation and dependency resolution

### Technical Requirements

**Schema Changes:**
- Modify `base_schema.py` to allow tasks without parent IDs
- Update validation logic to handle null/empty parent fields for standalone tasks
- Ensure task object validation works for both standalone and hierarchy-based tasks

**Path Resolution Updates:**
- Update `path_resolver.py` to handle `planning/tasks/` directory structure
- Modify `resolve_path_for_new_object()` to place standalone tasks in correct location
- Update `id_to_path()` and related functions to find standalone tasks

**Scanner Integration:**
- Modify `scanner.py` to scan `planning/tasks/` directory for standalone tasks
- Update `backlog_loader.py` to include standalone tasks in backlog queries
- Ensure filtering by scope, status, and priority works for standalone tasks

**Tool Integration:**
- Update `createObject` to handle standalone tasks (no parent validation)
- Modify `listBacklog()` to include standalone tasks in results
- Update `claimNextTask()` to consider standalone tasks in priority ordering
- Ensure `completeTask()` works with standalone task file paths

**Prerequisite System:**
- Enhance prerequisite validation to work across standalone and hierarchy-based tasks
- Update dependency graph building to include standalone tasks
- Ensure cycle detection works between all task types
- Maintain existing prerequisite completion checking (`is_unblocked()`)

### Implementation Phases

**Phase 1: Core Schema and Validation**
- Update base schema to allow tasks without parents
- Modify validation logic for standalone tasks
- Add comprehensive test coverage

**Phase 2: File System and Path Resolution**
- Update path resolution for `planning/tasks/` directory
- Modify scanner to include standalone tasks
- Test file creation and discovery

**Phase 3: Tool Integration**
- Update all MCP tools to handle standalone tasks
- Ensure backlog loading includes standalone tasks
- Test task claiming and completion workflows

**Phase 4: Cross-System Prerequisites**
- Enhance prerequisite validation for cross-system dependencies
- Update dependency graph building
- Test cycle detection across all task types

### Success Criteria
- Users can create tasks without creating projects/epics/features
- Standalone tasks integrate seamlessly with existing MCP tools
- Prerequisites work between standalone and hierarchy-based tasks
- No breaking changes to existing functionality
- Comprehensive test coverage for all new functionality

### Technical Constraints
- Maintain backward compatibility with existing hierarchy-based tasks
- Preserve existing file system organization patterns
- Ensure performance doesn't degrade with additional scanning
- Follow existing code patterns and conventions

### Log

