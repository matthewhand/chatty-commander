## 2024-05-24 - Optimize mask_sensitive_data
**Learning:** Generator expressions inside tight, recursive loops (like `any(p in str(k).lower() for p in sensitive_patterns)` in `mask_sensitive_data`) allocate a new generator on every recursion and loop iteration, which can be surprisingly slow due to python's generator overhead.
**Action:** Replace tight generator expressions with explicit `for` loops and `break` statements, and extract static collections to module-level tuples, to avoid allocation overhead when optimizing hot paths in highly recursive functions.
