---
description: Claim and implement a task following Research → Plan → Implement workflow
argument-hint: [task-id] --wt [worktree-path] [additional context or instructions]
---

# Implement Task Command

Claim and implement the next available task from the backlog using the Trellis task management system with the Research → Plan → Implement workflow.

## Trellis System Overview

The Trellis task management system organizes work in a hierarchical structure:

- **Projects**: Large-scale initiatives or products (e.g., "E-commerce Platform Redesign")
- **Epics**: Major work streams within a project (e.g., "User Authentication", "Payment Processing")
- **Features**: Specific functionality within epics (e.g., "Login Form", "Password Reset")
- **Tasks**: Atomic units of work, 1-2 hours each (e.g., "Create user model", "Add email validation")

This hierarchy enables parallel development, clear dependencies, and manageable work units.

## Goal

Automatically claim the highest-priority available task and implement it following project standards, with comprehensive research, planning, and quality checks before marking complete.

## Process

### 1. Claim Next Available Task

#### Input

`$ARGUMENTS` (optional) - Can specify:
- Specific task ID to claim (e.g., "T-create-user-model")
- Worktree path if using git worktrees
- Additional context or preferences

#### Instructions

If no specific task provided, use MCP `claimNextTask` to get the highest-priority available task.
If specific task ID provided, use MCP `getObject` and `updateObject` to claim it.

**Task claimed successfully:**
```
✅ Claimed task: T-create-user-model

📋 Task Details:
- Title: Create user database model with required fields
- Parent: F-user-registration
- Priority: High
- Status: Now in-progress

Let me research and plan before implementing...
```

**If no tasks available:**
```
❌ No available tasks found!

This could mean:
- All tasks are already claimed or completed
- All open tasks have incomplete prerequisites
- No tasks exist in the project

Check the backlog status or create new tasks for a feature.
```

### 2. Research Phase (MANDATORY)

**Never skip research - understand before coding:**

The research phase is critical for understanding the context and requirements before writing any code. During this phase:

- **Read parent objects for context**: Use MCP `getObject` to read the parent feature, epic, and project for additional context, specifications, and requirements that may not be fully detailed in the task description
- **Analyze project structure**: Explore the codebase to understand file organization, naming conventions, and architectural patterns
- **Study existing implementations**: Find similar code in the project to maintain consistency with established patterns
- **Research best practices**: Use the context7 MCP tool to access up-to-date documentation for libraries and frameworks
- **Use web search**: Search for current best practices, security considerations, and common pitfalls
- **Identify security requirements**: Consider authentication, authorization, input validation, and data protection needs
- **Review related code**: Examine interfaces this task will interact with to ensure compatibility
- **Check project documentation**: Look for CLAUDE.md, README files, or architecture docs for project-specific guidelines

```
📚 Research Phase for T-create-user-model

1️⃣ Reading parent objects for context...
   - Feature F-user-registration: Requires email/password fields, verification tokens
   - Epic E-user-management: Security standards, GDPR compliance requirements
   - Project P-ecommerce-platform: Tech stack (Node.js, Prisma, PostgreSQL)

2️⃣ Analyzing project structure...
   - Found existing models in: models/
   - Database: PostgreSQL with Prisma ORM
   - Pattern: One model per file

3️⃣ Checking similar implementations...
   - Reviewed: models/Post.js
   - Pattern: Class-based models with validation
   - Naming: PascalCase for models

4️⃣ Researching best practices...
   - Using context7 for Prisma documentation
   - Password handling: bcrypt with 12 rounds
   - UUID generation: native Prisma support

5️⃣ Security considerations...
   - Never store plain passwords
   - Email validation pattern required
   - Unique constraints on email/username

✅ Research complete. Creating implementation plan...
```

### 3. Plan Implementation

**Create detailed plan before coding:**

The planning phase translates research findings into a concrete implementation strategy. This phase should:

- **Define file structure**: Determine what files need to be created or modified
- **Sequence implementation steps**: Order tasks logically to avoid rework
- **Plan security measures**: Explicitly plan how to handle authentication, validation, and data protection
- **Design testing strategy**: Decide what tests are needed and how to structure them
- **Consider error handling**: Plan for edge cases and failure scenarios
- **Identify dependencies**: Note what needs to be imported or configured
- **Plan for maintainability**: Consider code organization, documentation, and future modifications

```
📝 Implementation Plan for T-create-user-model

1. File Structure:
   - models/User.js (model definition)
   - models/index.js (update barrel export)
   - migrations/001_create_users.sql

2. Implementation Steps:
   a) Create Prisma schema for User model
   b) Add field validations and constraints
   c) Generate migration files
   d) Create model wrapper with methods
   e) Write comprehensive tests
   f) Update documentation

3. Security Measures:
   - bcrypt for password hashing
   - Email regex validation
   - SQL injection prevention via ORM

4. Testing Strategy:
   - Unit tests for model methods
   - Validation edge cases
   - Unique constraint tests

Ready to implement with this plan.
```

### 4. Implementation Phase

**Execute the plan with progress updates:**

The implementation phase is where the actual coding happens. During this phase:

- **Follow the plan**: Execute the steps identified in the planning phase
- **Write clean code**: Follow project conventions and best practices
- **Implement incrementally**: Build and test small pieces before moving to the next
- **Run quality checks frequently**: Format, lint, and test after each major change
- **Write tests alongside code**: Don't leave testing for the end
- **Document as you go**: Add comments for complex logic or decisions
- **Apply security measures**: Implement validation, sanitization, and protection as planned
- **Handle errors gracefully**: Include proper error handling and user feedback

```
🔧 Implementing T-create-user-model

✓ Created models/User.js with Prisma schema
✓ Added field validations and constraints
✓ Generated migration: migrations/001_create_users.sql
✓ Implemented password hashing methods
✓ Added email validation
✓ Created comprehensive test suite

🧪 Running quality checks...
✅ Format: Clean
✅ Lint: 0 errors, 0 warnings  
✅ Type Check: Pass
✅ Tests: 12 passing, 0 failing
✅ Build: Success

📁 Files created/modified:
- models/User.js - User model with validation
- models/index.js - Added User export
- migrations/001_create_users.sql - Database schema
- tests/models/User.test.js - Comprehensive tests
```

### 5. Complete Task

**Update task and provide summary:**

The completion phase ensures the task is properly documented and marked as done. This phase includes:

- **Verify all requirements met**: Check that the implementation satisfies the task description
- **Confirm quality checks pass**: Ensure all tests, linting, and formatting are clean
- **Write meaningful summary**: Describe what was implemented and any important decisions
- **List all changed files**: Document what was created or modified
- **Update task status**: Use MCP to mark the task as complete
- **Note any follow-up needed**: Identify if additional tasks should be created

Use MCP `completeTask` with:
- Task ID
- Summary of work done
- List of files changed

Example for a database model task:
```
✅ Completing task: T-create-user-model

Summary:
Implemented User model with all required fields including secure password 
hashing, email validation, and unique constraints. Added comprehensive 
test coverage and database migrations. Password hashing uses bcrypt with 12 
rounds for security. Email validation includes regex pattern and uniqueness 
constraints. All tests passing with 100% coverage.

Files changed:
- models/User.js (new) - User model with validation methods
- models/index.js (modified) - Added User export
- migrations/001_create_users.sql (new) - Database schema
- tests/models/User.test.js (new) - Comprehensive test suite
- package.json (modified) - Added bcrypt dependency

✅ Task completed and moved to done folder!
```

Example for an API endpoint task:
```
✅ Completing task: T-register-endpoint

Summary:
Implemented POST /api/register endpoint with input validation, rate limiting, 
and secure password handling. Added email verification token generation and 
comprehensive error handling. Includes unit tests and integration tests with 
100% coverage. Rate limiting set to 5 attempts per minute per IP.

Files changed:
- routes/auth.js (new) - Registration endpoint with validation
- middleware/rateLimit.js (new) - Rate limiting middleware
- services/emailService.js (modified) - Added verification token generation
- tests/routes/auth.test.js (new) - Unit and integration tests
- tests/middleware/rateLimit.test.js (new) - Rate limiting tests
- config/email.js (modified) - Added token configuration

✅ Task completed and moved to done folder!
```

Example for a frontend component task:
```
✅ Completing task: T-registration-form

Summary:
Created registration form component with real-time validation, error handling, 
and accessibility features. Implements client-side validation with password 
strength indicator and email format checking. Added comprehensive test coverage 
including user interaction tests and accessibility compliance.

Files changed:
- components/RegistrationForm.jsx (new) - Main form component
- components/PasswordStrengthIndicator.jsx (new) - Password validation UI
- styles/RegistrationForm.module.css (new) - Component styles
- tests/components/RegistrationForm.test.jsx (new) - Component tests
- tests/components/PasswordStrengthIndicator.test.jsx (new) - Password tests
- utils/validation.js (modified) - Added client-side validation helpers

✅ Task completed and moved to done folder!
```

### 6. Next Steps

**Provide clear next actions:**

```
🎯 Task Complete: T-create-user-model

Next available task:
- T-add-user-validation: Add validation rules for user model
  (Depends on the task you just completed)

Run /implement-task again to claim and implement the next task.

Note: Your completed task has unblocked dependent tasks!
```

**STOP!** - Do not proceed. Complete one task and one task only. Do not implement another task.

## Error Handling

## Problem-Solving Framework

When you're stuck or confused:

1. **Stop** - Don't spiral into complex solutions
2. **Delegate** - Consider spawning agents for parallel investigation
3. **Think Deeply** - For complex problems, say "I need to think through this challenge"
4. **Step back** - Re-read the requirements and existing code
5. **Simplify** - The simple solution is usually correct
6. **Ask** - "I see two approaches: [A] vs [B]. Which do you prefer?"

When facing architectural decisions:

- Present options clearly with pros/cons
- Recommend the simpler approach
- Ask for guidance on trade-offs

### Use Multiple Agents

*Leverage subagents aggressively* for better results:

- Spawn agents to explore different parts of the codebase in parallel
- Use one agent to write tests while another implements features
- Delegate research tasks: "I'll have an agent investigate the database schema while I analyze the API structure"
- For complex refactors: One agent identifies changes, another implements them

Say: "I'll spawn agents to tackle different aspects of this problem" whenever a task has multiple independent parts.

### During Research Phase

```
⚠️ Research issue: Cannot find existing model patterns

Attempting alternative approaches:
- Checking documentation...
- Searching for examples...
- Using web search for best practices...

[If still stuck]
❓ Need clarification: 
The project doesn't seem to have existing models. 
Should I:
A) Create the first model and establish patterns
B) Check if models are in a different location
C) Use a different approach (raw SQL, different ORM)
```

### During Implementation

```
❌ Quality check failed: Linting errors found

models/User.js
  24:1  error  Multiple exports in file  one-export-per-file

🔧 Fixing quality issues...
✓ Split exports into separate files
✓ Re-running quality checks...
✅ All checks now passing!
```

### Blocked Tasks

```
⚠️ Cannot claim task: Prerequisites not met

Task T-api-tests requires:
- T-register-endpoint (in-progress)
- T-verify-endpoint (open)

These tasks must be completed first.
Searching for other available tasks...

✅ Found alternative: T-registration-form (frontend task)
This can be worked on in parallel.
```

## Security & Performance Principles

### Security Always:

- **Validate ALL inputs** - Never trust user data
- **Use secure defaults** - Fail closed, not open
- **Parameterized queries** - Never concatenate SQL/queries
- **Secure random** - Use cryptographically secure generators
- **Least privilege** - Request minimum permissions needed
- **Error handling** - Don't expose internal details

### Measure First:

- **No premature optimization** - Don't optimize unless specifically requested
- **No over-engineering** - Build only what's needed for the task
- **No extra features** - Don't add functionality that wasn't requested
- **Keep it simple** - Choose the most straightforward approach that works
- **Solve the actual problem** - Don't anticipate future requirements

### Forbidden Patterns:

- **NO "any" types** - Use specific, concrete types
- **NO sleep/wait loops** - Use proper async patterns
- **NO keeping old and new code together** - Delete replaced code immediately
- **NO custom error hierarchies** - Keep errors simple
- **NO hardcoded secrets or environment values**
- **NO concatenating user input into queries** - Use parameterized queries

### Modular Code Architecture:

- **Clear boundaries** - Each module/class/function should have a single, well-defined responsibility
- **Minimal coupling** - Components should interact through clean interfaces, not internal implementation details
- **High cohesion** - Related functionality should be grouped together in the same module
- **Dependency injection** - Use interfaces and dependency injection instead of tight coupling
- **Avoid big ball of mud** - Prevent tangled cross-dependencies between modules
- **Clean interfaces** - Define clear contracts (APIs) between components
- **Separation of concerns** - Keep business logic, data access, and UI separate
- **Avoid circular dependencies** - Structure code to have clear dependency flow

## Quality Standards

During implementation, ensure:

- **Research First**: Never skip research phase
- **One Export Per File**: Enforced by linting
- **Test Coverage**: Write tests in same task
- **Security**: Validate all inputs
- **Documentation**: Comment complex logic
- **Quality Checks**: All must pass before completion

## Communication Standards

### Progress Updates:

```
✓ Researched existing patterns
✓ Implemented authentication (all tests passing)
✓ Added input validation
✗ Found issue with token expiration - investigating
```

### Quality Check Results:

```
✅ Format: Clean
✅ Lint: 0 errors, 0 warnings
✅ Type Check: Pass
✅ Tests: 42 passing, 0 failing
✅ Build: Success
```

### Suggesting Improvements:

"The current approach works, but I notice [observation].
Would you like me to [specific improvement]?"

## Common Implementation Patterns

### Database Models
```
Research: Check existing models, ORM patterns
Plan: Schema, validations, migrations, tests
Implement: Model → Migration → Tests → Exports
```

### API Endpoints
```
Research: RESTful patterns, auth middleware
Plan: Route, validation, errors, tests
Implement: Route → Handler → Tests → Docs
```

### Frontend Components
```
Research: Component patterns, state management
Plan: Props, state, events, styling, tests
Implement: Component → Styles → Tests → Story
```

## Workflow Guidelines

- Always follow Research → Plan → Implement
- Run quality checks after each major change
- Write tests alongside implementation
- Commit only when all checks pass
- Document decisions in code comments

<rules>
  <critical>ALWAYS follow Research → Plan → Implement workflow</critical>
  <critical>NEVER skip quality checks before completing task</critical>
  <critical>All tests must pass before marking task complete</critical>
  <critical>One export per file rule must be followed</critical>
  <critical>Never modify any planning or task files directly - always use the Trellis MCP commands</critical>
  <important>Use context7 for library documentation</important>
  <important>Search codebase for patterns before implementing</important>
  <important>Write tests in the same task as implementation</important>
  <important>Apply security best practices to all code</important>
  <important>Update task with meaningful summary when complete</important>
</rules>