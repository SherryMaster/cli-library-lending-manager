# Loan lifecycle

Checkout creates a historical `Loan` that references an existing book and
member by their stored stable IDs. Loan IDs use the same trimmed,
case-insensitive matching rule as other entity IDs.

The lending period is exactly 14 calendar days:

```text
due date = checkout date + 14 days
```

Normal checkout and return operations use `date.today()`. They also accept an
explicit date so date boundaries can be tested deterministically.

A book may have at most one active loan. Return replaces the immutable active
record with a completed record containing `returned_date`; it never deletes the
loan. A loan may be returned exactly once, and its returned date cannot precede
its checkout date.

`LibraryState` centralizes active-loan and availability queries. Availability
is derived: a known book is available exactly when it has no active loan. No
availability or loan-status flag is stored separately.
