---
kind: task
id: T-add-scope-filtering-capability
title: Add scope filtering capability to task scanner
status: open
priority: high
prerequisites:
- T-extend-filterparams-model-to
created: '2025-07-20T13:19:48.083515'
updated: '2025-07-20T13:19:48.083515'
schema_version: '1.1'
parent: F-scope-based-task-filtering
---
## Context

The scanner.py module currently provides `scan_tasks()` for all tasks and `filter_by_scope()` is used in listBacklog. We need to enhance the scanner to support scope-aware task discovery that respects hierarchical boundaries for claimNextTask functionality.

## Implementation Requirements

### Enhance existing filter_by_scope function
- Extend `filter_by_scope()` in `src/trellis_mcp/scanner.py` to support claiming workflow
- Add scope boundary resolution for P-, E-, F- prefixed scope IDs
- Maintain existing cross-system compatibility (hierarchical tasks only, standalone unaffected)

### Scope boundary logic implementation
```python
def resolve_scope_boundaries(scope_id: str, scanning_root: Path) -> list[Path]:
    """Resolve scope ID to task directory paths within boundaries."""
    if scope_id.startswith('P-'):
        # Project scope: all tasks within project hierarchy
        return list((scanning_root / "projects" / scope_id).rglob("tasks-*"))
    elif scope_id.startswith('E-'):
        # Epic scope: all tasks within epic and its features  
        return list((scanning_root / "projects" / "*" / "epics" / scope_id).rglob("tasks-*"))
    elif scope_id.startswith('F-'):
        # Feature scope: only tasks directly within feature
        return list((scanning_root / "projects" / "*" / "epics" / "*" / "features" / scope_id / "tasks-*"))
    else:
        raise ValueError(f"Invalid scope prefix: {scope_id}")
```

### Integration with kind inference
- Use KindInferenceEngine to validate scope object existence before filtering
- Follow pattern from other tools: `inference_engine.infer_kind(scope_id, validate=True)`
- Raise ValidationError if scope object doesn't exist

### Error handling patterns
- Return empty iterator when scope contains no tasks (graceful handling)
- Validate scope object exists using kind inference before scanning
- Follow existing error resilience patterns in scanner

## Acceptance Criteria

- [ ] filter_by_scope() supports P-, E-, F- scope boundary resolution
- [ ] Project scope includes all tasks within project hierarchy
- [ ] Epic scope includes all tasks within epic and its features
- [ ] Feature scope includes only direct tasks within feature
- [ ] Scope validation uses kind inference engine
- [ ] Empty scope results handled gracefully
- [ ] Cross-system compatibility maintained (standalone tasks unaffected)

## Testing Requirements

Create unit tests in `tests/test_scanner.py`:
- Scope boundary resolution for each scope type
- Empty scope handling (scope exists but no tasks)
- Invalid scope object validation
- Cross-system task discovery with scope filtering
- Path traversal security validation

## Dependencies

- Requires T-extend-filterparams-model-to for scope parameter validation
- Uses existing KindInferenceEngine for scope validation

## Files to Modify

- `src/trellis_mcp/scanner.py`: Enhance filter_by_scope() with scope boundaries
- `tests/test_scanner.py`: Add scope filtering test coverage

### Log

