## 2024-04-21 - Caching `str.lower()` in comprehensions for performance
**Learning:** Re-evaluating `str(k).lower()` inside a comprehension directly inside `any(...)` causes an O(N) evaluation of `.lower()` for every item evaluated. This is especially impactful in recursive loops or large sets.
**Action:** Extract repeated string evaluations or static method calls outside loops or generator expressions to significantly reduce overhead.
