---
description: Break down a feature into specific, actionable tasks (1-2 hours each)
argument-hint: [feature-id] [additional context or instructions]
---

# Create Tasks Command

Break down a feature into specific, actionable tasks using the Trellis task management system.

## Trellis System Overview

The Trellis task management system organizes work in a hierarchical structure:

- **Projects**: Large-scale initiatives or products (e.g., "E-commerce Platform Redesign")
- **Epics**: Major work streams within a project (e.g., "User Authentication", "Payment Processing")
- **Features**: Specific functionality within epics (e.g., "Login Form", "Password Reset")
- **Tasks**: Atomic units of work, 1-2 hours each (e.g., "Create user model", "Add email validation")

This hierarchy enables parallel development, clear dependencies, and manageable work units.

## Goal

Analyze a feature's comprehensive specification to create granular tasks that can be individually claimed and completed by developers, ensuring complete implementation of the feature with proper testing and security considerations.

## Process

### 1. Identify Target Feature

#### Input

`$ARGUMENTS`

#### Feature Context

The feature ID may be:
- Provided in `input` (e.g., "F-user-registration")
- Known from previous conversation context
- Specified along with additional instructions in `input`

#### Instructions

Retrieve the feature using MCP `getObject` to access its comprehensive description, requirements, and parent epic/project context.

### 2. Analyze Feature Specification

**Thoroughly analyze the feature description to identify required tasks:**

- **Use context7 MCP tool** to research implementation patterns and best practices
- **Search codebase** for similar task patterns or implementations
- Extract all components and deliverables from the feature description
- Review implementation guidance and technical approach
- Identify testing requirements for comprehensive coverage
- Consider security considerations that need implementation
- Analyze performance requirements and constraints
- Group related implementation work
- Identify task dependencies and sequencing
- Note any specific instructions provided in `input`

### 3. Gather Additional Information

**Ask clarifying questions as needed to refine the task breakdown:**

Use this structured approach:
- **Ask one question at a time** with specific options
- **Focus on task boundaries** - understand what constitutes a complete, testable task
- **Identify implementation details** - specific technical approaches or patterns
- **Continue until complete** - don't stop until you have clear task structure

Key areas to clarify:
- **Implementation Details**: Specific technical approaches or patterns?
- **Task Boundaries**: What constitutes a complete, testable task?
- **Dependencies**: Which tasks must complete before others?
- **Testing Approach**: Unit tests, integration tests, or both?
- **Security Implementation**: How to handle validation and authorization?

**Example questioning approach:**
```
How should the user model validation be implemented?
Options:
- A) Basic field validation only (required fields, data types)
- B) Advanced validation with custom rules and error messages
- C) Validation with integration to existing validation framework
```

Continue until the task structure:
- Covers all aspects of the feature specification
- Represents atomic units of work (1-2 hours each)
- Has clear implementation boundaries
- Includes adequate testing and security tasks

### 4. Generate Task Structure

For each task, create:
- **Title**: Clear, actionable description
- **Description**: Detailed explanation including:
  - **Detailed Context**: Enough information for a developer new to the project to complete the work, including:
    - Links to relevant specifications, documentation, or other Trellis objects (tasks, features, epics, projects)
    - References to existing patterns or similar implementations in the codebase
    - Specific technologies, frameworks, or libraries to use
    - File paths and component locations where work should be done
  - **Specific implementation requirements**: What exactly needs to be built
  - **Technical approach to follow**: Step-by-step guidance on implementation
  - **Detailed Acceptance Criteria**: Specific, measurable requirements that define project success, including:
    - Functional deliverables with clear success metrics
    - Performance benchmarks (response times, throughput, capacity)
    - Security requirements and compliance standards
    - User experience criteria and usability standards
    - Integration testing requirements with external systems
    - Deployment and operational readiness criteria
  - **Dependencies on other tasks**: Prerequisites and sequencing
  - **Security considerations**: Validation, authorization, and protection requirements
  - **Testing requirements**: Specific tests to write and coverage expectations

**Task Granularity Guidelines:**

Each task should be sized appropriately for implementation:
- **1-2 hours per task** - Tasks should be completable in one sitting
- **Atomic units of work** - Each task should produce a meaningful, testable change
- **Independent implementation** - Tasks should be workable without blocking others
- **Specific scope** - Implementation approach should be clear from the task description
- **Testable outcome** - Tasks should have defined acceptance criteria

**Default task hierarchy approach:**
- **Prefer flat structure** - Most tasks should be at the same level
- **Only create sub-tasks when necessary** - When a task is genuinely too large (>2 hours)
- **Keep it simple** - Avoid unnecessary complexity in task organization

Group tasks logically:
- **Setup/Configuration**: Initial setup tasks
- **Core Implementation**: Main functionality (includes unit tests and documentation)
- **Security**: Validation and protection (includes related tests and docs)

### 5. Create Tasks Using MCP

For each task, call the Task Trellis MCP `createObject` tool:

- `projectRoot`: Current working directory
- `kind`: Set to `"task"`
- `parent`: The feature ID
- `title`: Generated task title
- `status`: Set to `"open"`
- `priority`: Based on criticality and dependencies
- `prerequisites`: List of task IDs that must complete first
- `description`: Comprehensive task description

### 6. Output Format

After successful creation:

```
✅ Successfully created [N] tasks for feature "[Feature Title]"

📋 Created Tasks:
Database & Models:
  ✓ T-[id1]: Create user database model with validation and unit tests
  ✓ T-[id2]: Add email verification token system with tests and docs

API Development:
  ✓ T-[id3]: Create POST /api/register endpoint with tests and validation
  ✓ T-[id4]: Implement email verification endpoint with tests
  ✓ T-[id5]: Add rate limiting with monitoring and tests

Frontend:
  ✓ T-[id6]: Create registration form component with tests and error handling
  ✓ T-[id7]: Add client-side validation with unit tests
  ✓ T-[id8]: Implement success/error states with component tests

Integration:
  ✓ T-[id9]: Write end-to-end integration tests for full registration flow

📊 Task Summary:
- Total Tasks: [N]
- High Priority: [X]
- Dependencies Configured: ✓

Next step:
Use /implement-task to claim and work on the next available task
```

## Example Task Structures

### User Registration Feature

```
Setup & Configuration:
  - Create user database model with required fields, validation, and unit tests
  - Set up email service configuration with error handling and tests

API Development:
  - Create POST /api/register endpoint with input validation, tests, and docs
  - Implement email verification token generation with security tests
  - Create GET /api/verify-email endpoint with validation and integration tests
  - Add rate limiting to registration endpoint with monitoring and tests

Frontend Components:
  - Create registration form component with unit tests and error handling
  - Add client-side validation with comprehensive test coverage
  - Implement success/error states with component tests
  - Create email verification page with user flow tests

Security Implementation:
  - Add input sanitization for user data with security tests and docs
  - Implement CAPTCHA integration with validation tests
  - Add password strength validation with comprehensive test suite
```

### API Integration Feature

```
Configuration:
  - Set up API client configuration with validation and documentation
  - Create environment variables for API keys with security tests

Implementation:
  - Create API client service class with unit tests and comprehensive docs
  - Implement authentication method with security tests and error handling
  - Create data transformation layer with validation tests and examples
  - Add retry logic with exponential backoff, monitoring, and tests

Error Handling:
  - Implement error response parsing with unit tests and documentation
  - Create fallback mechanisms with reliability tests
  - Add logging for API calls with log level tests and docs

Performance & Integration:
  - Write comprehensive integration test suite with real API scenarios
  - Add performance tests for rate limits and response times
```

## Task Creation Guidelines

Ensure tasks are:
- **Atomic**: Completable in one sitting (1-2 hours)
- **Specific**: Clear implementation path
- **Testable**: Defined acceptance criteria
- **Independent**: Minimal coupling where possible
- **Secure**: Include necessary validations

Common task patterns:
- **Model/Schema**: Create with validation, indexing, unit tests, and docs
- **API Endpoint**: Implement with input validation, error handling, tests, and docs
- **Frontend Component**: Create with interactivity, state handling, tests, and docs
- **Security**: Input validation, authorization, rate limiting with tests and docs

## Simplicity Principles

When creating tasks, follow these guidelines:

### Keep It Simple:
- **No over-engineering** - Create only the tasks needed for the feature
- **No extra features** - Don't add functionality that wasn't requested
- **Choose straightforward approaches** - Simple task structure over complex designs
- **Solve the actual problem** - Don't anticipate future requirements

### Forbidden Patterns:
- **NO premature optimization** - Don't optimize task structure unless requested
- **NO feature creep** - Stick to the specified feature requirements
- **NO complex dependencies** - Keep task relationships simple and clear
- **NO unnecessary abstractions** - Choose direct, maintainable approaches

### Modular Architecture:
- **Clear boundaries** - Each task should have distinct, well-defined responsibilities
- **Minimal coupling** - Tasks should create components that interact through clean interfaces
- **High cohesion** - Related functionality should be grouped within the same task/component
- **Avoid big ball of mud** - Prevent tangled cross-dependencies between components
- **Clean interfaces** - Create clear contracts between components for data and functionality exchange

## Question Guidelines

Ask questions that:
- **Clarify implementation**: Specific libraries or approaches?
- **Define boundaries**: What's included in each task?
- **Identify prerequisites**: What must be built first?
- **Confirm testing strategy**: What types of tests are needed?

## Priority Assignment

Assign priorities based on:
- **High**: Blocking other work, security-critical, core functionality
- **Normal**: Standard implementation tasks
- **Low**: Enhancements, optimizations, nice-to-have features

## Error Handling

- **Feature not found**: Provide clear error message
- **Invalid dependencies**: Detect and prevent circular dependencies
- **Missing feature description**: Request feature details be added first

<rules>
  <critical>Feature ID is required (from arguments or context)</critical>
  <critical>Base task breakdown primarily on feature description</critical>
  <critical>Never directly access `planning/` directory</critical>
  <critical>Use MCP tools for all operations</critical>
  <critical>Each task must be completable in 1-2 hours</critical>
  <critical>Ask one question at a time with specific options</critical>
  <critical>Continue asking questions until you have complete understanding of task boundaries</critical>
  <important>Use context7 MCP tool to research implementation patterns and best practices</important>
  <important>Include testing and documentation within implementation tasks</important>
  <important>Add security validation with tests where applicable</important>
  <important>Configure dependencies to enable parallel work</important>
  <important>Follow project patterns identified in feature</important>
  <important>Prefer flat task structure - only create sub-tasks when necessary</important>
</rules>