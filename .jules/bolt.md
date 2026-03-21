## 2024-03-02 - [React Callback In-place Array Slice Bottleneck]
**Learning:** Frequent array creation operations (like `.slice(-MAX_MESSAGES)`) executed inline within a React state setter callback triggered by high-frequency events (like WebSockets) cause multiple rapid allocations/destructuring that can block the main thread.
**Action:** When working with high-frequency WebSocket data streams in React, conditionally slice the array before allocating a new copy (e.g. `prev.length >= MAX_MESSAGES ? [...prev.slice(1), msg] : [...prev, msg]`) to skip redundant operations, or use a circular buffer pattern for maximum efficiency.

## 2024-03-01 - [CommandsList React Render Optimization]
**Learning:** In a dashboard where real-time Websocket data causes frequent global re-renders, mapping objects directly inside JSX using `Object.entries()` without memoization can cause unexpected performance degradation because array reallocation forces React to fully re-reconcile that subtree despite matching keys.
**Action:** When deriving arrays from objects in React (`Object.entries`, `Object.keys`, `Object.values`), always wrap the transformation in `useMemo` if the parent component is subject to frequent re-renders from polling or websockets.

## 2026-03-21 - [State Setter Callback Reallocation Optimizations]
**Learning:** In high-frequency React state updates using WebSockets, spreading the result of an inline array slice (`[...prev.slice(1), item]`) causes unnecessary memory allocations and object creation. The array is sliced, then immediately spread into a new array.
**Action:** When working with high-frequency WebSocket data streams in React, conditionally check if the array needs slicing and only slice it when necessary, then assign the result to a variable (`newPrev`), and finally spread that into the new state (`[...newPrev, item]`). This prevents creating multiple disposable objects inside the setter callback and is much more efficient.
