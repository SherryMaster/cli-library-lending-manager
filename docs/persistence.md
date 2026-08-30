# Persistence and recovery

The default application file is `data/library.json`. `JsonLibraryStore`
converts between that JSON document and `LibraryState`; generic filesystem and
atomic-write behavior remains in `JsonStorage`.

The top-level JSON object contains exactly the canonical collections used by
the application: `books`, `members`, and complete `loans` history. Dates use
ISO `YYYY-MM-DD` text. Derived availability, active/overdue flags, and totals
are not stored.

A missing file is a valid first launch and produces an empty state. Successful
mutations notify the store immediately, and `JsonStorage` writes a temporary
file before replacing the canonical file.

Loading validates top-level shape, record fields and dates, case-insensitive
duplicate IDs, active relationship references, and the one-active-loan-per-book
invariant. Malformed or invalid data is never silently overwritten. Startup
offers an unsaved temporary session; choosing it leaves the bad file untouched.
