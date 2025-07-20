---
kind: task
id: T-extend-filterparams-model-to
title: Extend FilterParams model to support scope parameter validation
status: open
priority: high
prerequisites: []
created: '2025-07-20T13:19:30.378115'
updated: '2025-07-20T13:19:30.378115'
schema_version: '1.1'
parent: F-scope-based-task-filtering
---
## Context

The FilterParams model in `src/trellis_mcp/models/filter_params.py` currently handles status and priority filtering. Following the pattern established in listBacklog tool, we need to extend it to support scope parameter validation for hierarchical boundaries (P-, E-, F- prefixed IDs).

## Implementation Requirements

### Add scope field to FilterParams class
- Add optional `scope: str | None = None` field to FilterParams model
- Create field validator `validate_scope_format()` that checks for valid P-, E-, F- prefix patterns
- Use regex pattern validation: `^[PEF]-[A-Za-z0-9_-]+$`
- Return clear validation error for invalid scope format

### Scope validation logic
```python
@field_validator('scope')
@classmethod
def validate_scope_format(cls, v: str | None) -> str | None:
    if v is None:
        return v
    if not re.match(r'^[PEF]-[A-Za-z0-9_-]+$', v):
        raise ValueError(f"Invalid scope ID format: {v}")
    return v
```

### Integration with existing patterns
- Follow same validation approach as status/priority validators
- Maintain backward compatibility with existing FilterParams usage
- Scope parameter should be optional (None means no scope filtering)

## Acceptance Criteria

- [ ] FilterParams model accepts scope parameter with P-, E-, F- validation
- [ ] Invalid scope formats raise clear ValueError messages  
- [ ] Existing FilterParams usage continues to work unchanged
- [ ] Unit tests cover scope validation edge cases
- [ ] Documentation updated for new scope parameter

## Testing Requirements

Create unit tests in `tests/models/test_filter_params.py`:
- Valid scope formats: "P-project", "E-epic", "F-feature"
- Invalid formats: no prefix, wrong prefix, special characters
- None/empty scope handling
- Error message clarity and consistency

## Dependencies

None - this is foundational validation that other tasks will build upon.

## Files to Modify

- `src/trellis_mcp/models/filter_params.py`: Add scope field and validation
- `tests/models/test_filter_params.py`: Add scope validation tests

### Log

