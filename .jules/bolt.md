## 2024-03-02 - [React Callback In-place Array Slice Bottleneck]
**Learning:** Frequent array creation operations (like `.slice(-MAX_MESSAGES)`) executed inline within a React state setter callback triggered by high-frequency events (like WebSockets) cause multiple rapid allocations/destructuring that can block the main thread.
**Action:** When working with high-frequency WebSocket data streams in React, conditionally slice the array before allocating a new copy (e.g. `prev.length >= MAX_MESSAGES ? [...prev.slice(1), msg] : [...prev, msg]`) to skip redundant operations, or use a circular buffer pattern for maximum efficiency.

## 2024-03-01 - [CommandsList React Render Optimization]
**Learning:** In a dashboard where real-time Websocket data causes frequent global re-renders, mapping objects directly inside JSX using `Object.entries()` without memoization can cause unexpected performance degradation because array reallocation forces React to fully re-reconcile that subtree despite matching keys.
**Action:** When deriving arrays from objects in React (`Object.entries`, `Object.keys`, `Object.values`), always wrap the transformation in `useMemo` if the parent component is subject to frequent re-renders from polling or websockets.

## 2024-03-03 - [Ignored Memoized State in React]
**Learning:** In `DashboardPage.tsx`, a `useMemo` hook was correctly implemented to prevent array reallocation (`messages.slice(-15)`) during high-frequency WebSocket events, but the memoized value was inadvertently omitted from the JSX render function. This negates the optimization and continues to cause unnecessary array allocations on the main thread.
**Action:** Always verify that memoized values (`useMemo`, `useCallback`) are actually consumed in the render output or dependency arrays. Creating a memoized value alone does not automatically optimize the inline operations it was meant to replace.
