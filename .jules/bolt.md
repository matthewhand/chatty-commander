## 2024-03-02 - [React Callback In-place Array Slice Bottleneck]
**Learning:** Frequent array creation operations (like `.slice(-MAX_MESSAGES)`) executed inline within a React state setter callback triggered by high-frequency events (like WebSockets) cause multiple rapid allocations/destructuring that can block the main thread.
**Action:** When working with high-frequency WebSocket data streams in React, conditionally slice the array before allocating a new copy (e.g. `prev.length >= MAX_MESSAGES ? [...prev.slice(1), msg] : [...prev, msg]`) to skip redundant operations, or use a circular buffer pattern for maximum efficiency.

## 2024-03-01 - [CommandsList React Render Optimization]
**Learning:** In a dashboard where real-time Websocket data causes frequent global re-renders, mapping objects directly inside JSX using `Object.entries()` without memoization can cause unexpected performance degradation because array reallocation forces React to fully re-reconcile that subtree despite matching keys.
**Action:** When deriving arrays from objects in React (`Object.entries`, `Object.keys`, `Object.values`), always wrap the transformation in `useMemo` if the parent component is subject to frequent re-renders from polling or websockets.

## 2024-03-18 - [LLM Command Processor Matcher Optimization]
**Learning:** High-frequency validation/matching loops (e.g., matching keywords to available commands in `_simple_command_matching`) can slow down significantly due to redundant allocations (like `.lower()`) and repeated iteration over large dict views (`.items()`).
**Action:** Pre-compute cached lowercase dict keys and pre-filter relationship maps into simple dictionaries during class instantiation/initialization. Iterating over keys directly is also slightly faster than allocating view objects with `.items()`.

## 2024-03-30 - [React Component Reallocation on High-Frequency Renders]
**Learning:** Refactoring a ternary inline array slice (e.g., `prev.length >= MAX ? [...prev.slice(1), item] : [...prev, item]`) to a conditionally sliced variable provides absolutely no measurable performance improvement because the ternary operator guarantees only one branch executes. The real bottleneck is mapping arrays to JSX elements (like `agentData?.map(...)`) inside a parent component (`DashboardPage`) that re-renders rapidly due to unrelated WebSocket state updates (`messages`, `history`).
**Action:** When a parent component receives high-frequency real-time updates, identify mapped JSX element lists that depend on stable or less-frequent data. Wrap the array mapping in a `useMemo` hook (e.g., `const listRender = useMemo(() => data.map(...), [data])`) to prevent React from unnecessarily re-allocating those Virtual DOM objects on every parent render tick. Always include in-code comments explaining the optimization.
