## 2024-03-03 - [Numpy 1D Array Sum of Squares Bottleneck]
**Learning:** In hot paths (like voice activity detection) calculating the energy of a 1D audio array using `np.sum(arr ** 2)` forces Numpy to allocate a large intermediate memory array for `arr ** 2` before summation.
**Action:** When calculating the sum of squares for 1D arrays in Python/NumPy, prefer `np.dot(arr, arr)` over `np.sum(arr ** 2)`. This avoids the intermediate allocation overhead and leverages optimized C-level BLAS routines, significantly improving execution speed (~3-4x faster).

## 2024-03-02 - [React Callback In-place Array Slice Bottleneck]
**Learning:** Frequent array creation operations (like `.slice(-MAX_MESSAGES)`) executed inline within a React state setter callback triggered by high-frequency events (like WebSockets) cause multiple rapid allocations/destructuring that can block the main thread.
**Action:** When working with high-frequency WebSocket data streams in React, conditionally slice the array before allocating a new copy (e.g. `prev.length >= MAX_MESSAGES ? [...prev.slice(1), msg] : [...prev, msg]`) to skip redundant operations, or use a circular buffer pattern for maximum efficiency.

## 2024-03-01 - [CommandsList React Render Optimization]
**Learning:** In a dashboard where real-time Websocket data causes frequent global re-renders, mapping objects directly inside JSX using `Object.entries()` without memoization can cause unexpected performance degradation because array reallocation forces React to fully re-reconcile that subtree despite matching keys.
**Action:** When deriving arrays from objects in React (`Object.entries`, `Object.keys`, `Object.values`), always wrap the transformation in `useMemo` if the parent component is subject to frequent re-renders from polling or websockets.
