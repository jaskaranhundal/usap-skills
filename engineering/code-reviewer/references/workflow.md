# Code Reviewer Workflow

## Pre-Review

1. Read PR description and linked issue/ticket
2. Understand the intended change and acceptance criteria
3. Review any linked design doc or ADR

## Phase 1: Architecture Review

1. Check if the change aligns with existing architectural patterns
2. Identify coupling violations or layer boundary breaches
3. Flag SOLID principle violations (especially Single Responsibility, Open/Closed)
4. Review API design for consistency with existing endpoints

## Phase 2: Performance Review

1. Scan for N+1 query patterns (ORM loops, lazy loading in list views)
2. Check for missing database indexes on newly queried columns
3. Identify blocking I/O in async code paths
4. Review algorithmic complexity of new functions (flag cyclomatic complexity > 10)

## Phase 3: Security Surface Check

1. Verify authorization checks on new state-changing endpoints
2. Check input validation presence at system boundaries
3. Flag obvious insecure patterns — escalate to appsec-code-review for deep analysis

## Phase 4: Test Coverage Review

1. Identify all new functions and branches introduced
2. Verify unit tests exist for new logic
3. Check edge cases: null inputs, empty collections, boundary values
4. Review test naming for clarity

## Phase 5: Review Decision

1. Classify each finding by severity (critical / high / medium / low)
2. Apply review decision logic
3. Draft developer-friendly feedback for each finding
4. Submit structured review output
