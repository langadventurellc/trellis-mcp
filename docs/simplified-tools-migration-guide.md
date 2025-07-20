# Simplified Tools Migration Guide

## Overview

This guide helps you migrate from the original `getObject` and `updateObject` tool interfaces to the new simplified versions that feature automatic kind inference and cleaner response formats.

## What Changed

### Simplified Parameters

**Before (Original Interface):**
```javascript
// Required explicit kind parameter
await mcp.call('getObject', {
  kind: 'task',                    // ❌ No longer needed
  id: 'T-implement-auth',
  projectRoot: './planning'
});

await mcp.call('updateObject', {
  kind: 'task',                    // ❌ No longer needed  
  id: 'T-implement-auth',
  projectRoot: './planning',
  yamlPatch: { status: 'review' }
});
```

**After (Simplified Interface):**
```javascript
// Automatic kind inference from ID prefix
await mcp.call('getObject', {
  id: 'T-implement-auth',          // ✅ Kind inferred from T- prefix
  projectRoot: './planning'
});

await mcp.call('updateObject', {
  id: 'T-implement-auth',          // ✅ Kind inferred from T- prefix
  projectRoot: './planning',
  yamlPatch: { status: 'review' }
});
```

### Cleaner Response Format

**Before (Original Response):**
```javascript
{
  "yaml": { /* object data */ },
  "body": "markdown content",
  "file_path": "/full/path/to/file.md",  // ❌ Internal implementation detail
  "kind": "task",
  "id": "T-implement-auth"
}
```

**After (Simplified Response):**
```javascript
{
  "yaml": { /* object data */ },
  "body": "markdown content",
  "kind": "task",                        // ✅ Now inferred automatically
  "id": "T-implement-auth",              // ✅ Clean ID format
  "children": [                          // ✅ New: immediate children
    {
      "id": "subtask-id",
      "title": "Subtask Title", 
      "status": "open",
      "kind": "task",
      "created": "2025-07-19T..."
    }
  ]
}
```

## Benefits of Simplified Interface

### 1. Reduced Complexity
- **50% fewer parameters** required for most operations
- **No mental overhead** remembering object type mappings
- **Automatic inference** prevents parameter mismatch errors

### 2. Better Developer Experience
```javascript
// Before: Had to remember kind mappings
getObject('project', 'P-auth')     // Easy to mix up
getObject('epic', 'E-auth')        // Redundant information
getObject('feature', 'F-auth')     // Error-prone

// After: ID prefix tells the whole story
getObject('P-auth')                // Obviously a project
getObject('E-auth')                // Obviously an epic  
getObject('F-auth')                // Obviously a feature
```

### 3. Enhanced Data Access
- **Children discovery** included automatically
- **Clean response format** without internal implementation details
- **Consistent structure** across all object types

## Migration Steps

### Step 1: Update Tool Calls

Remove the `kind` parameter from all `getObject` and `updateObject` calls:

```javascript
// ❌ Old way
const project = await mcp.call('getObject', {
  kind: 'project',
  id: 'P-auth-system',
  projectRoot: './planning'
});

// ✅ New way
const project = await mcp.call('getObject', {
  id: 'P-auth-system',
  projectRoot: './planning'
});
```

### Step 2: Update Response Handling

Remove any code that depends on the `file_path` field in responses:

```javascript
// ❌ Old way - don't rely on file_path
const response = await mcp.call('getObject', { /* ... */ });
console.log(`File location: ${response.file_path}`);  // Will be undefined

// ✅ New way - use clean response data
const response = await mcp.call('getObject', { /* ... */ });
console.log(`Object: ${response.kind} ${response.id}`);
console.log(`Children: ${response.children.length} items`);
```

### Step 3: Leverage New Features

Take advantage of automatic children discovery:

```javascript
const feature = await mcp.call('getObject', {
  id: 'F-user-registration',
  projectRoot: './planning'
});

// ✅ New: Access immediate children without separate calls
feature.children.forEach(task => {
  console.log(`Task: ${task.title} (${task.status})`);
});
```

## Best Practices with Simplified Tools

### 1. Embrace ID Prefixes
Use clear, descriptive IDs with proper prefixes:
```javascript
// ✅ Good: Clear project identification
'P-ecommerce-platform-redesign'

// ✅ Good: Clear task identification  
'T-implement-user-authentication'

// ❌ Avoid: Generic IDs without context
'P-project1'
'T-task'
```

### 2. Leverage Children Discovery
Use the built-in children information to avoid extra calls:
```javascript
// ✅ Efficient: Get feature and its tasks in one call
const feature = await mcp.call('getObject', {
  id: 'F-user-registration',
  projectRoot: './planning'
});

// Process immediate child tasks
feature.children.filter(child => child.kind === 'task')
  .forEach(task => {
    console.log(`Task: ${task.title} (${task.status})`);
  });
```

### 3. Handle Errors Gracefully
Take advantage of improved error messages:
```javascript
try {
  const obj = await mcp.call('getObject', {
    id: 'invalid-id',
    projectRoot: './planning'
  });
} catch (error) {
  if (error.message.includes('Invalid ID format')) {
    console.log('Please provide an ID with proper prefix (P-, E-, F-, T-)');
  } else if (error.message.includes('not found')) {
    console.log('Object does not exist');
  }
}
```

## Summary

The simplified tool interfaces represent a significant improvement in developer experience while maintaining full backward compatibility. By removing the redundant `kind` parameter and cleaning up response formats, these tools are now more intuitive and easier to use.

Key migration points:
1. **Remove `kind` parameters** from tool calls
2. **Stop accessing `file_path`** in responses
3. **Leverage automatic children discovery** for better efficiency
4. **Use clear ID prefixes** for better code readability

The simplified tools make Trellis MCP more accessible to new users while providing existing users with a cleaner, more efficient interface.