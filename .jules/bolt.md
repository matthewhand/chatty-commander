## 2024-03-02 - [React Callback In-place Array Slice Bottleneck]
**Learning:** Frequent array creation operations (like `.slice(-MAX_MESSAGES)`) executed inline within a React state setter callback triggered by high-frequency events (like WebSockets) cause multiple rapid allocations/destructuring that can block the main thread.
**Action:** When working with high-frequency WebSocket data streams in React, conditionally slice the array before allocating a new copy (e.g. `prev.length >= MAX_MESSAGES ? [...prev.slice(1), msg] : [...prev, msg]`) to skip redundant operations, or use a circular buffer pattern for maximum efficiency.

## 2024-03-01 - [CommandsList React Render Optimization]
**Learning:** In a dashboard where real-time Websocket data causes frequent global re-renders, mapping objects directly inside JSX using `Object.entries()` without memoization can cause unexpected performance degradation because array reallocation forces React to fully re-reconcile that subtree despite matching keys.
**Action:** When deriving arrays from objects in React (`Object.entries`, `Object.keys`, `Object.values`), always wrap the transformation in `useMemo` if the parent component is subject to frequent re-renders from polling or websockets.

## 2024-03-18 - [LLM Command Processor Matcher Optimization]
**Learning:** High-frequency validation/matching loops (e.g., matching keywords to available commands in `_simple_command_matching`) can slow down significantly due to redundant allocations (like `.lower()`) and repeated iteration over large dict views (`.items()`).
**Action:** Pre-compute cached lowercase dict keys and pre-filter relationship maps into simple dictionaries during class instantiation/initialization. Iterating over keys directly is also slightly faster than allocating view objects with `.items()`.

## 2024-03-29 - [LLM Command Processor Suggestions Optimization]
**Learning:** High-frequency input handling, such as fetching command suggestions based on partial input via `get_command_suggestions`, suffers from performance bottlenecks when repeatedly allocating lowercase copies of string descriptions inside loops (`desc.lower()`).
**Action:** Pre-compute and cache lowercase string values during initialization (`_available_suggestions_map` from `SUGGESTION_MAP`) so the application avoids allocating new string instances in real-time user input loops. Iterating over pre-computed lower-case items directly avoids the redundant allocations.

## 2024-04-19 - [HTTP Streaming Response Size Limit Bottleneck]
**Learning:** When enforcing a size limit on streaming HTTP responses (e.g., via `httpx.stream`), iterating using `response.iter_text()` and calculating size via `len(chunk.encode("utf-8"))` inside the loop causes high CPU overhead due to repeated string encoding.
**Action:** Iterate over byte chunks directly using `response.iter_bytes()`, accumulate size via `len(chunk)`, append to a list, and perform a single decode at the end (`b"".join(pieces).decode(...)`). This significantly improves performance for responses with non-ASCII content.
