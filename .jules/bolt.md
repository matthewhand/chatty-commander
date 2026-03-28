## 2024-03-28 - [Unused Memoization Value Bottleneck]
**Learning:** In React components with high-frequency re-renders (like WebSocket-driven dashboards), it's a common anti-pattern to compute a memoized array (e.g., using `useMemo` for `.slice(-MAX)`) but then fail to actually consume that memoized value in the JSX render output. Unused memoized values fail to prevent the inline reallocations they were intended to optimize, causing unnecessary main thread overhead.
**Action:** When implementing memoized arrays or derived states in React components, explicitly verify that the memoized value is consumed within the JSX, replacing any direct `inline.map` or `inline.slice` usage with the memoized constant.

## 2024-03-02 - [React Callback In-place Array Slice Bottleneck]
**Learning:** Frequent array creation operations (like `.slice(-MAX_MESSAGES)`) executed inline within a React state setter callback triggered by high-frequency events (like WebSockets) cause multiple rapid allocations/destructuring that can block the main thread.
**Action:** When working with high-frequency WebSocket data streams in React, conditionally slice the array before allocating a new copy (e.g. `prev.length >= MAX_MESSAGES ? [...prev.slice(1), msg] : [...prev, msg]`) to skip redundant operations, or use a circular buffer pattern for maximum efficiency.

## 2024-03-01 - [CommandsList React Render Optimization]
**Learning:** In a dashboard where real-time Websocket data causes frequent global re-renders, mapping objects directly inside JSX using `Object.entries()` without memoization can cause unexpected performance degradation because array reallocation forces React to fully re-reconcile that subtree despite matching keys.
**Action:** When deriving arrays from objects in React (`Object.entries`, `Object.keys`, `Object.values`), always wrap the transformation in `useMemo` if the parent component is subject to frequent re-renders from polling or websockets.
