## 2024-03-02 - [React Callback In-place Array Slice Bottleneck]
**Learning:** Frequent array creation operations (like `.slice(-MAX_MESSAGES)`) executed inline within a React state setter callback triggered by high-frequency events (like WebSockets) cause multiple rapid allocations/destructuring that can block the main thread.
**Action:** When working with high-frequency WebSocket data streams in React, conditionally slice the array before allocating a new copy (e.g. `prev.length >= MAX_MESSAGES ? [...prev.slice(1), msg] : [...prev, msg]`) to skip redundant operations, or use a circular buffer pattern for maximum efficiency.

## 2024-03-01 - [CommandsList React Render Optimization]
**Learning:** In a dashboard where real-time Websocket data causes frequent global re-renders, mapping objects directly inside JSX using `Object.entries()` without memoization can cause unexpected performance degradation because array reallocation forces React to fully re-reconcile that subtree despite matching keys.
**Action:** When deriving arrays from objects in React (`Object.entries`, `Object.keys`, `Object.values`), always wrap the transformation in `useMemo` if the parent component is subject to frequent re-renders from polling or websockets.

## 2024-03-09 - [DashboardPage React Render Optimization]
**Learning:** Even if a derived array is correctly memoized using `useMemo`, using an inline `.slice()` mapping directly in the render function (e.g., `messages.slice(-15).map(...)`) circumvents the memoization. This results in the creation of a new array reference on every render, triggering unnecessary reconciliation of mapped child elements—particularly problematic in components handling high-frequency WebSocket updates.
**Action:** When deriving data using `useMemo` specifically to avoid inline operations during frequent re-renders, ensure the memoized variable is directly used in the JSX map function rather than reapplying the transformation to the original un-memoized source data.
