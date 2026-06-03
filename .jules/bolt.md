## 2024-03-02 - [React Callback In-place Array Slice Bottleneck]
**Learning:** Frequent array creation operations (like `.slice(-MAX_MESSAGES)`) executed inline within a React state setter callback triggered by high-frequency events (like WebSockets) cause multiple rapid allocations/destructuring that can block the main thread.
**Action:** When working with high-frequency WebSocket data streams in React, conditionally slice the array before allocating a new copy (e.g. `prev.length >= MAX_MESSAGES ? [...prev.slice(1), msg] : [...prev, msg]`) to skip redundant operations, or use a circular buffer pattern for maximum efficiency.

## 2024-03-01 - [CommandsList React Render Optimization]
**Learning:** In a dashboard where real-time Websocket data causes frequent global re-renders, mapping objects directly inside JSX using `Object.entries()` without memoization can cause unexpected performance degradation because array reallocation forces React to fully re-reconcile that subtree despite matching keys.
**Action:** When deriving arrays from objects in React (`Object.entries`, `Object.keys`, `Object.values`), always wrap the transformation in `useMemo` if the parent component is subject to frequent re-renders from polling or websockets.

## 2024-03-03 - [Python O(1) Set Membership Optimization]
**Learning:** In Python 3.12+, membership checks using set literals (`in {"a", "b"}`) are optimized into `frozenset` constants during compilation, providing O(1) lookup time. This is measurably faster (~5% for small sets) than tuple or list membership checks which require O(N) linear scans.
**Action:** Prefer set literals for direct membership checks (`if x in {"val1", "val2"}:`) in performance-critical paths. However, avoid this for iteration patterns like `any(word in text for word in collection)`, as iteration over sets provides no O(1) benefit and may lose frequency-based short-circuiting advantages.
