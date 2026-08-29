# Canonical in-memory data model

While the program is running, library data is represented by domain objects,
not by JSON dictionaries or presentation-specific values.

## Canonical records

- `Book`: stable `id`, `title`, `author`, and `category`.
- `Member`: stable `id` and `name`.
- `Loan`: stable `id`, referenced `book_id` and `member_id`, `checkout_date`,
  `due_date`, and optional `returned_date`.
- `LibraryState`: owns the book, member, and complete loan-history collections.

`Loan.returned_date` is the source of truth for return status. A loan is active
when that value is `None`. Returned loans remain in `LibraryState.loans` so
history is not lost.

Availability flags, overdue flags, and aggregate totals are deliberately not
fields in this model. They will be derived from canonical loan records, which
prevents contradictory state such as a book marked available while it has an
active loan.

The records are immutable value objects. Later update and return operations can
validate a complete replacement before changing the relevant collection. The
`LibraryState` container is mutable because application operations will add,
replace, and remove validated records over the life of the process.

## Decisions intentionally deferred

The roadmap defines separate tasks for these concerns, so this model does not
yet decide or implement them:

- identifier normalization, case sensitivity, lookup, and duplicate detection;
- blank-field validation and CRUD operations;
- checkout, due-date, and return mutations;
- JSON serialization and recovery;
- search, ordering, derived views, and statistics.
