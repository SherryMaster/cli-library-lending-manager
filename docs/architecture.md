# Architecture boundaries

- `domain` owns library records, identifier rules, and lending invariants.
- `application` will coordinate use cases and declares the capabilities it
  needs through small interfaces such as `Storage`.
- `persistence` contains technical adapters. `JsonStorage` satisfies the
  `Storage` interface because it provides compatible `load()` and `save()`
  methods; no inheritance is required.
- `presentation` owns terminal input, output, and the reusable `Menu` classes.
- `bootstrap.py` constructs concrete objects and connects the layers.

The intended direction is:

```text
presentation -> application -> domain
                         ^
                         |
                   persistence
```

`Menu` remains presentation-only and `JsonStorage` remains generic. Neither
contains book, member, loan, or lending rules.
