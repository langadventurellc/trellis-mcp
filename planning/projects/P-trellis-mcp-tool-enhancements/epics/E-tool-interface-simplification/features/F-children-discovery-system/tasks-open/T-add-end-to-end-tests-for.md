---
kind: task
id: T-add-end-to-end-tests-for
title: Add end-to-end tests for getObject enhancement with children array validation
status: open
priority: normal
prerequisites:
- T-write-comprehensive-integratio-1
created: '2025-07-19T19:04:55.032220'
updated: '2025-07-19T19:04:55.032220'
schema_version: '1.1'
parent: F-children-discovery-system
---
# Add End-to-End Tests for getObject Enhancement

## Context
Create comprehensive end-to-end tests that validate the complete getObject enhancement workflow from MCP tool calls through children array validation, ensuring the entire system works correctly in realistic usage scenarios. Do not write performance tests; focus on end-to-end testing patterns and workflows.

## Technical Approach
Implement end-to-end tests that:
- Test actual MCP tool invocations through the FastMCP framework
- Validate complete request/response cycles including children arrays
- Test real-world usage patterns and client interactions
- Follow end-to-end testing patterns from existing MCP tool tests
- Include error scenarios and edge cases in realistic contexts

## Specific Implementation Requirements

### Test Suite Structure (in `tests/e2e/test_getobject_children_e2e.py`)
```python
class TestGetObjectChildrenEndToEnd:
    """End-to-end tests for getObject tool enhancement with children arrays.
    
    Tests complete MCP tool workflows including request processing, children
    discovery, response formatting, and error handling through the FastMCP
    framework with realistic client interaction patterns.
    """
    
    def test_getobject_project_with_children_e2e(self):
        """Test complete getObject workflow for project with epics."""
        
    def test_getobject_epic_with_children_e2e(self):
        """Test complete getObject workflow for epic with features."""
        
    def test_getobject_feature_with_children_e2e(self):
        """Test complete getObject workflow for feature with tasks."""
        
    def test_getobject_task_no_children_e2e(self):
        """Test complete getObject workflow for task (no children)."""
        
    def test_getobject_error_scenarios_e2e(self):
        """Test error handling in complete getObject workflows."""
```

### MCP Tool Integration Testing
Test actual tool invocations using the FastMCP framework:
```python
# Tool invocation pattern
async def invoke_getobject_tool(server, kind: str, id: str, project_root: str):
    """Invoke getObject tool through MCP protocol."""
    result = await server.call_tool(
        name="getObject",
        arguments={
            "kind": kind,
            "id": id, 
            "projectRoot": project_root
        }
    )
    return result
```

### End-to-End Test Scenarios
```python
e2e_test_scenarios = [
    # Standard workflows
    {
        "name": "project_standard_workflow",
        "request": {"kind": "project", "id": "sample-project", "projectRoot": "/test/path"},
        "expected_response": {
            "yaml": dict,
            "body": str,
            "file_path": str,
            "kind": "project",
            "id": "sample-project",
            "children": list  # Array of epic objects
        },
        "children_validation": {
            "count": 3,
            "types": ["epic"],
            "required_fields": ["id", "title", "status", "kind", "created", "file_path"]
        }
    },
    
    # Edge cases
    {
        "name": "empty_project_workflow",
        "request": {"kind": "project", "id": "empty-project", "projectRoot": "/test/path"},
        "expected_response": {
            "children": []  # Empty array for project with no epics
        }
    },
    
    # Error scenarios
    {
        "name": "nonexistent_object_workflow",
        "request": {"kind": "project", "id": "nonexistent", "projectRoot": "/test/path"},
        "expected_error": "FileNotFoundError",
        "error_validation": {
            "error_type": "object_not_found",
            "error_message_contains": "Project with ID 'nonexistent' not found"
        }
    }
]
```

### Response Validation Framework
```python
class ResponseValidator:
    """Comprehensive validation for getObject responses with children."""
    
    def validate_response_structure(self, response: dict) -> bool:
        """Validate response has all required fields and correct types."""
        
    def validate_children_array(self, children: list[dict]) -> bool:
        """Validate children array structure and metadata."""
        
    def validate_parent_child_consistency(self, parent: dict, children: list[dict]) -> bool:
        """Validate parent-child relationships are logically consistent."""
```

## Detailed Acceptance Criteria

### Complete Workflow Validation
- [ ] **MCP Protocol**: Tool calls work correctly through FastMCP framework
- [ ] **Request Processing**: All getObject parameters processed correctly
- [ ] **Response Format**: Responses match expected MCP tool response format
- [ ] **Children Integration**: Children arrays correctly included in all responses
- [ ] **Error Handling**: Error responses follow MCP protocol conventions

### Client Interaction Scenarios
- [ ] **Standard Usage**: Typical client getObject calls return expected results
- [ ] **Batch Operations**: Multiple sequential getObject calls work correctly
- [ ] **Concurrent Requests**: Simultaneous getObject calls from multiple clients
- [ ] **Long-Running Sessions**: Extended client sessions with repeated calls
- [ ] **Error Recovery**: Clients can recover from error responses appropriately

### Data Consistency Validation
- [ ] **Parent Metadata**: Parent object data correctly retrieved and formatted
- [ ] **Children Metadata**: All child objects have complete, accurate metadata
- [ ] **Relationship Integrity**: Parent-child relationships are logically consistent
- [ ] **Type Safety**: All objects have correct type information and formatting
- [ ] **Timestamp Consistency**: Creation dates and ordering are accurate

## Testing Requirements

### End-to-End Test Infrastructure
```python
# E2E test setup and teardown
@pytest.fixture
async def mcp_server_with_test_project(tmp_path):
    """Set up complete MCP server with test project for E2E testing."""
    # Create test project structure
    # Initialize MCP server with getObject tool
    # Return configured server instance
```

### Realistic Test Data
- **Production-Like Projects**: Test data mirrors real-world project complexity
- **Edge Case Projects**: Empty projects, single-child projects, deeply nested projects
- **Error Scenario Projects**: Projects with missing files, permission issues, corrupted data

### Client Simulation
```python
class MockMCPClient:
    """Simulate realistic MCP client interactions."""
    
    async def simulate_typical_usage(self, server):
        """Simulate typical client usage patterns."""
        # Navigation workflows: project → epic → feature → task
        # Repeated queries with caching
        # Error handling and recovery
```

### Validation Scenarios
```python
# Comprehensive validation test matrix
validation_matrix = {
    "parent_types": ["project", "epic", "feature", "task"],
    "children_scenarios": ["none", "single", "multiple", "many"],
    "client_patterns": ["single_call", "navigation_sequence", "repeated_calls"],
    "error_conditions": ["missing_object", "corrupted_data", "permission_denied"],
}
```

## Implementation Guidance

### Test Execution Patterns
```python
async def test_complete_navigation_workflow(self, mcp_server):
    """Test complete client navigation through project hierarchy."""
    # 1. Get project with children (epics)
    project_response = await invoke_getobject_tool(
        mcp_server, "project", "sample-project", "/test/path"
    )
    validate_project_response_with_children(project_response)
    
    # 2. Navigate to first epic with children (features)  
    first_epic_id = project_response["children"][0]["id"]
    epic_response = await invoke_getobject_tool(
        mcp_server, "epic", first_epic_id, "/test/path"
    )
    validate_epic_response_with_children(epic_response)
    
    # 3. Navigate to first feature with children (tasks)
    first_feature_id = epic_response["children"][0]["id"]
    feature_response = await invoke_getobject_tool(
        mcp_server, "feature", first_feature_id, "/test/path"
    )
    validate_feature_response_with_children(feature_response)
    
    # 4. Navigate to first task (no children)
    first_task_id = feature_response["children"][0]["id"]
    task_response = await invoke_getobject_tool(
        mcp_server, "task", first_task_id, "/test/path"
    )
    validate_task_response_no_children(task_response)
```

### Error Scenario Testing
- **Network Simulation**: Simulate network delays and failures
- **Resource Constraints**: Test under memory and CPU pressure
- **File System Issues**: Simulate permission errors and disk full scenarios
- **Concurrent Conflicts**: Test with simultaneous file modifications

## Documentation Requirements
- [ ] **E2E Test Guide**: How to run and interpret end-to-end tests
- [ ] **Client Integration Examples**: Sample code showing proper getObject usage
- [ ] **Troubleshooting Guide**: Common E2E test failures and resolution steps

### Example Client Usage Documentation
```python
# Example: Navigating project hierarchy with enhanced getObject
async def navigate_project_hierarchy(mcp_client, project_id):
    """Example client usage of enhanced getObject with children."""
    
    # Get project and its immediate epics
    project = await mcp_client.call_tool("getObject", {
        "kind": "project",
        "id": project_id,
        "projectRoot": "/project/path"
    })
    
    print(f"Project: {project['yaml']['title']}")
    print(f"Epics: {len(project['children'])}")
    
    # Navigate to each epic and show features
    for epic_child in project['children']:
        epic = await mcp_client.call_tool("getObject", {
            "kind": "epic", 
            "id": epic_child['id'],
            "projectRoot": "/project/path"
        })
        
        print(f"  Epic: {epic['yaml']['title']}")
        print(f"  Features: {len(epic['children'])}")
        
        # Navigate to features and show tasks
        for feature_child in epic['children']:
            feature = await mcp_client.call_tool("getObject", {
                "kind": "feature",
                "id": feature_child['id'], 
                "projectRoot": "/project/path"
            })
            
            print(f"    Feature: {feature['yaml']['title']}")
            print(f"    Tasks: {len(feature['children'])}")
```

## Dependencies
- Successful completion of T-write-comprehensive-integratio-1 (integration tests)
- FastMCP framework for MCP tool testing
- Test project structures and fixtures from integration tests

### Log

