---
kind: task
id: T-implement-error-message
parent: F-enhanced-error-handling
status: done
title: Implement error message templates system
priority: high
prerequisites:
- T-create-custom-exception-classes
created: '2025-07-18T10:25:42.277617'
updated: '2025-07-18T10:55:28.958934'
schema_version: '1.1'
worktree: null
---
Create a system for error message templates with placeholder substitution to ensure consistent, user-friendly error messages.

**Implementation Details:**
- Create error message templates for common validation failures
- Implement template engine with placeholder substitution
- Support context-aware messages for standalone vs hierarchy tasks
- Include localization support for future internationalization
- Create message formatting utilities

**Acceptance Criteria:**
- Error message templates are created for all validation scenarios
- Template system supports placeholder substitution
- Context-aware messaging works for different task types
- Localization framework is in place
- Message formatting is consistent and user-friendly

**Dependencies:** Custom exception classes must be implemented first

### Log


**2025-07-18T16:07:05.806930Z** - Implemented comprehensive error message template system with centralized templates, parameter substitution, context awareness, and backward compatibility. Created 40+ message templates covering all validation scenarios including status, parent, security, hierarchy, and field validation. Integrated with existing validation functions while maintaining full backward compatibility.
- filesChanged: ["src/trellis_mcp/validation/message_templates/__init__.py", "src/trellis_mcp/validation/message_templates/core.py", "src/trellis_mcp/validation/message_templates/registry.py", "src/trellis_mcp/validation/message_templates/templates.py", "src/trellis_mcp/validation/message_templates/formatters.py", "src/trellis_mcp/validation/message_templates/engine.py", "src/trellis_mcp/validation/context_utils.py", "src/trellis_mcp/validation/security.py", "tests/unit/test_message_templates.py"]