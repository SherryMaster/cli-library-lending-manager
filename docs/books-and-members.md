# Books and members

`application.Library` owns the validated book and member workflows while
`domain.LibraryState` owns the in-memory collections.

- Add operations trim every field, reject blanks and equivalent duplicate IDs,
  and append only after all validation succeeds.
- Exact lookup delegates to `LibraryState` and uses the shared stable-ID rule.
- Text search is partial and case-insensitive across title, author, and category
  for books, and name for members. It is separate from exact ID lookup.
- Updates replace immutable records only after all new values are valid. Stable
  IDs are preserved.
- Removal first checks active loans. Returned historical loans remain recorded
  and do not block removal.

These operations have no terminal input/output and no JSON knowledge. Future
presentation code can call them without owning library correctness rules.
