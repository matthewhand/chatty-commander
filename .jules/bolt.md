## 2024-03-02 - [React Callback In-place Array Slice Bottleneck]
**Learning:** Frequent array creation operations (like `.slice(-MAX_MESSAGES)`) executed inline within a React state setter callback triggered by high-frequency events (like WebSockets) cause multiple rapid allocations/destructuring that can block the main thread.
**Action:** When working with high-frequency WebSocket data streams in React, conditionally slice the array before allocating a new copy (e.g. `prev.length >= MAX_MESSAGES ? [...prev.slice(1), msg] : [...prev, msg]`) to skip redundant operations, or use a circular buffer pattern for maximum efficiency.

## 2024-03-01 - [CommandsList React Render Optimization]
**Learning:** In a dashboard where real-time Websocket data causes frequent global re-renders, mapping objects directly inside JSX using `Object.entries()` without memoization can cause unexpected performance degradation because array reallocation forces React to fully re-reconcile that subtree despite matching keys.
**Action:** When deriving arrays from objects in React (`Object.entries`, `Object.keys`, `Object.values`), always wrap the transformation in `useMemo` if the parent component is subject to frequent re-renders from polling or websockets.

## 2024-03-18 - [LLM Command Processor Matcher Optimization]
**Learning:** High-frequency validation/matching loops (e.g., matching keywords to available commands in `_simple_command_matching`) can slow down significantly due to redundant allocations (like `.lower()`) and repeated iteration over large dict views (`.items()`).
**Action:** Pre-compute cached lowercase dict keys and pre-filter relationship maps into simple dictionaries during class instantiation/initialization. Iterating over keys directly is also slightly faster than allocating view objects with `.items()`.
## 2024-04-11 - [Config Payload Iteration Optimization]
**Learning:** Iterating over an unbounded user-provided payload (like a JSON dictionary via `config_data.items()`) during filtering is inefficient (O(M)) and opens a small window for processing delay attacks. Iterating over the application's strict, fixed allowlist set (O(K)) instead is mathematically faster and safer.
**Action:** When applying a fixed allowlist to an input dictionary in Python, iterate over the allowlist keys (e.g., `{k: input[k] for k in ALLOWLIST if k in input}`) rather than the input dictionary items.
## 2026-04-12 - [Module-Level Variable Imports]
**Learning:** When a code review flags missing imports or predicts `NameError`s on startup, always verify their presence in the target file using bash commands (e.g., `grep`) before attempting a fix, as the reviewer's context may be hallucinated or outdated.
**Action:** Use grep to check for imports like `import threading` and `from typing import Any` before assuming they are missing.
## 2026-04-29 - [React useMemo Conditonal Rendering Bottleneck]
**Learning:** When using `useMemo` to optimize mapped JSX elements in React (e.g., `data?.map(...)`), declaring the hook inline within JSX conditional rendering blocks (e.g., ternaries) causes `react-hooks/rules-of-hooks` violations. Additionally, if helper functions used inside the map are recreated on every render, the memoization will be invalidated.
**Action:** Declare the hook at the top level of the component after the data is defined. Extract static helper functions used inside the map outside the component entirely, or wrap them in `useCallback`.
