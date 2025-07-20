---
kind: task
id: T-update-tool-documentation-and
title: Update tool documentation and usage examples
status: open
priority: low
prerequisites:
- T-write-comprehensive-integratio-2
created: '2025-07-19T20:25:31.174397'
updated: '2025-07-19T20:25:31.174397'
schema_version: '1.1'
parent: F-object-tool-simplification
---
## Purpose

Update tool documentation, docstrings, and usage examples to reflect the simplified getObject and updateObject interfaces, providing clear migration guidance and demonstrating the improved developer experience.

## Context

After implementing and testing the simplified tools, documentation must be updated to reflect the new interfaces. This includes updating docstrings, creating usage examples, and providing migration guidance for users transitioning from the original tools.

**Reference files:**
- Current tool docstrings in simplified implementations
- Any existing documentation files in `docs/` directory
- README files and usage examples
- Tool registration descriptions and metadata

**Technologies to use:**
- Markdown for documentation files
- Python docstrings following project conventions
- Code examples demonstrating simplified interfaces

## Implementation Requirements

### 1. Update Tool Docstrings
Ensure simplified tool docstrings accurately reflect new interfaces:
```python
def getObject(id: str, projectRoot: str):
    """Retrieve a Trellis MCP object by ID with automatic kind inference.
    
    Automatically detects object type from ID prefix, eliminating the need
    for explicit kind parameters. Returns clean response format focused
    on object data without internal file system details.
    
    Args:
        id: Object ID with prefix (P-, E-, F-, T-)
        projectRoot: Root directory for planning structure
        
    Returns:
        Dictionary with object data (yaml, body, kind, id, children)
        Note: file_path no longer included for cleaner interface
        
    Examples:
        >>> getObject("P-auth-system", "./planning")
        >>> getObject("T-implement-login", "./planning")
    """
```

### 2. Create Migration Documentation
Document the transition from original to simplified tools:
- Parameter changes (removal of `kind` parameter)
- Response format changes (removal of `file_path`)
- Benefits of simplified interface
- Code examples showing before/after usage

### 3. Update Usage Examples
Create comprehensive usage examples demonstrating:
- Basic object retrieval with simplified getObject
- Object updates with simplified updateObject
- Error handling with new interface
- Integration with kind inference

### 4. Update Tool Metadata
Ensure tool registration includes accurate descriptions:
- Clear parameter descriptions
- Updated tool descriptions emphasizing simplification
- Migration guidance in tool metadata
- Examples of proper usage

## Detailed Implementation Steps

### Step 1: Audit Current Documentation
1. Locate all documentation references to getObject and updateObject
2. Identify docstrings, README files, and usage examples
3. Note any API documentation or specification files
4. Create inventory of documentation to update

### Step 2: Update Tool Docstrings
1. Review simplified tool implementations for docstring accuracy
2. Ensure parameter descriptions reflect simplified interface
3. Update return value documentation to exclude file_path
4. Add migration notes and usage examples to docstrings

### Step 3: Create Migration Guide
1. Document parameter changes and rationale
2. Provide before/after code examples
3. Explain response format changes
4. Include troubleshooting guidance for common migration issues

### Step 4: Update Usage Examples
1. Create examples for all object types (P-, E-, F-, T-)
2. Show error handling scenarios
3. Demonstrate integration with other tools
4. Include performance and best practice guidance

### Step 5: Update Project Documentation
1. Update README files to reflect simplified interfaces
2. Update any API documentation or specifications
3. Update tool registration descriptions
4. Ensure consistency across all documentation

## Acceptance Criteria

### Documentation Quality Requirements
- [ ] **Accuracy**: All documentation accurately reflects simplified interfaces
- [ ] **Completeness**: All tool parameters and return values are documented
- [ ] **Clarity**: Documentation is clear and easy to understand
- [ ] **Examples**: Comprehensive examples demonstrate proper usage
- [ ] **Migration Guidance**: Clear guidance for transitioning from original tools

### Content Requirements
- [ ] **Parameter Documentation**: Clear description of simplified parameters
- [ ] **Response Format**: Accurate documentation of clean response format
- [ ] **Error Handling**: Documentation of error scenarios and messages
- [ ] **Performance Notes**: Any performance implications of simplified interface
- [ ] **Best Practices**: Guidance on optimal usage patterns

### User Experience Requirements
- [ ] **Developer Onboarding**: New developers can understand and use tools quickly
- [ ] **Migration Support**: Existing users can transition smoothly to simplified tools
- [ ] **Troubleshooting**: Common issues and solutions are documented
- [ ] **Code Examples**: Examples are practical and copy-pasteable
- [ ] **Consistency**: Documentation style is consistent across all tools

## Documentation Categories

### 1. API Documentation
```markdown
## getObject(id, projectRoot)

Retrieve any Trellis object by ID with automatic type detection.

### Parameters
- `id` (string): Object ID with type prefix (P-, E-, F-, T-)
- `projectRoot` (string): Planning directory path

### Returns
Object data with inferred type information (excludes internal file paths)

### Examples
```python
# Get a project
project = getObject("P-auth-system", "./planning")

# Get a task  
task = getObject("T-implement-login", "./planning")
```

### 2. Migration Guide
```markdown
## Migrating to Simplified Tools

### Before (Original Interface)
```python
getObject(kind="project", id="P-auth-system", projectRoot="./planning")
```

### After (Simplified Interface)  
```python
getObject(id="P-auth-system", projectRoot="./planning")
```

### Key Changes
1. **Removed `kind` parameter** - now inferred automatically
2. **Cleaner responses** - no internal `file_path` field
3. **Same functionality** - all features preserved
```

### 3. Error Handling Guide
```markdown
## Error Handling

### Invalid ID Format
```python
try:
    obj = getObject("invalid-id", "./planning")
except ValidationError as e:
    print(f"Invalid ID format: {e}")
```

### Object Not Found
```python
try:
    obj = getObject("P-nonexistent", "./planning")  
except FileNotFoundError as e:
    print(f"Object not found: {e}")
```
```

## Content Guidelines

### Writing Style
- **Clear and Concise**: Use simple, direct language
- **Example-Driven**: Include practical examples for all concepts
- **User-Focused**: Write from the developer's perspective
- **Migration-Friendly**: Help users transition smoothly

### Code Examples
- **Working Examples**: All code examples should be runnable
- **Error Handling**: Include error handling in examples
- **Best Practices**: Demonstrate recommended usage patterns
- **Performance**: Include performance considerations where relevant

### Organization
- **Logical Flow**: Information presented in logical order
- **Cross-References**: Link related concepts and tools
- **Searchable**: Use clear headings and keywords
- **Versioning**: Note version information where applicable

## Files to Create or Update

### Primary Documentation Files
- Tool docstrings in simplified implementations
- README files with updated usage examples
- Migration guide documentation
- API reference documentation

### Supporting Documentation
- Error handling guides
- Best practices documentation
- Performance considerations
- Integration examples

## Quality Assurance

### Documentation Review
- Technical accuracy review
- Style and clarity review
- Example validation (ensure examples work)
- User experience review

### Testing Documentation
- Verify all code examples work correctly
- Test migration examples with actual code
- Validate error handling examples
- Check documentation completeness

## Success Metrics

### User Adoption Metrics
- Reduced support questions about tool usage
- Faster developer onboarding with simplified tools
- Positive feedback on documentation clarity
- Successful migration from original tools

### Documentation Quality Metrics
- Complete coverage of all tool features
- Accurate and up-to-date information
- Clear, actionable examples
- Comprehensive migration guidance

This documentation update ensures that users can quickly understand and adopt the simplified tools, while providing comprehensive guidance for migration from the original interfaces.

### Log

