# WebRTC Audio Bridge — Feasibility Spike (ROADMAP P2)

Status: **SPIKE / findings only.** No production code changed. This document maps
what is feasible vs. speculative for the ROADMAP item "WebRTC audio bridge"
(`ROADMAP.md:125`). The honest verdict is up front; the evidence follows.

## TL;DR verdict

- **Phase 0 (state-only bridge): buildable today.** Poll `get_workflow_run`
  (`dograh_client.py:221`), map dograh run state → `StateManager.change_state`
  (`state_manager.py:117`), which already broadcasts over `/ws` as a
  `state_change` message (`web_mode.py:936`). No shared audio, no new dograh
  capability needed. Delivers visible value (call state in the CC UI badge).
- **Shared-audio barge-in: feasible in principle but blocked / high-risk.** It
  depends on dograh capabilities we have *not verified against a live instance*
  — whether dograh's `smallwebrtc` peer can ingest an *externally supplied*
  audio track, and whether dograh exposes a *push* event stream (vs. polling)
  for call state. Both are unknowns, and the providers (STT/TTS/LLM) the audio
  path needs are not yet wired (`ROADMAP.md:101`).
- The wakeword→handoff path also presumes CC even *has* the live mic stream to
  hand off, which today it only does in the local in-process pipeline, not in
  the browser-SPA + container topology where dograh calls actually run.

---

## 1. Current state — and where the two audio worlds are SEPARATE

### 1a. CC's local voice stack (in-process Python)

- Audio capture is **in-process via PyAudio**, opened directly on the host's
  default input device: `pyaudio.PyAudio().open(format=paInt16, channels=1,
  rate=16000, frames_per_buffer=1280)` (`voice/wakeword.py:127`). Frame format
  is **16 kHz, 16-bit mono PCM, 1280-sample (80 ms) chunks** (`wakeword.py:58`).
- Threading model: a single daemon thread runs `_listen_loop`
  (`wakeword.py:137`,`:172`) that reads chunks, runs `openwakeword.Model.predict`
  (`wakeword.py:194`), and fires registered callbacks on detection
  (`wakeword.py:211`).
- The pipeline (`voice/pipeline.py:48`) wires wakeword → transcription → command
  match → `CommandExecutor.execute_command` (`pipeline.py:299`), and drives
  `StateManager.change_state(...)` for its *own* sub-states
  (`voice_listening`/`voice_recording`/`voice_processing`, `pipeline.py:118`,
  `:166`, `:221`).
- In the orchestrator path, the wakeword callback is routed differently: a
  detection becomes a *command* `wake_word_<name>` dispatched to the command sink
  (`orchestrator.py:283`–`:301`), not directly a state transition.

Key point: **CC's audio never leaves the Python process.** There is no encoder,
no WebRTC peer, no network audio track. The mic bytes are consumed locally and
discarded after prediction.

### 1b. dograh's audio (separate container, terminates in the browser)

- dograh runs as a **separate docker stack** (`dograh_client.py:2`,
  `docker-compose.dograh.yml`). CC talks to it only over **REST**
  (`DograhClient`, `dograh_client.py:105`); the only methods that exist are
  health, workflow list/fetch, `initiate_call`, `create_workflow_run`,
  `list_workflow_runs`, `get_workflow_run` (`dograh_client.py:131`–`:229`).
- dograh's actual *audio* path is **pipecat + WebRTC (`smallwebrtc`)** and the
  call leg is a **WebRTC peer in the browser** — proven by the loopback spec:
  "dograh ships a smallwebrtc mode where the call leg is a WebRTC peer in the
  browser" (`dograh_webcall_loopback.spec.ts:5`–`:11`). The browser opens a
  signaling WS to `/api/v1/ws/signaling` and exchanges SDP/ICE
  (`dograh_webcall_loopback.spec.ts:74`–`:91`). A `smallwebrtc` run is created
  with `{"mode":"smallwebrtc"}` (`dograh_webcall_loopback.spec.ts:20`–`:22`).

Key point: **dograh's audio terminates in the user's browser tab**, against
dograh's own backend. CC's Python process is not in that media path at all.

### 1c. The integration boundary (precise)

```
   CC (Python, in-process)              dograh (separate container)
   ┌───────────────────────┐           ┌──────────────────────────┐
   │ PyAudio mic → openww   │           │ pipecat pipeline          │
   │ → StateManager/Executor│  REST     │ STT→LLM→TTS               │
   │ DograhClient ──────────┼──────────►│ /telephony, /workflow,    │
   └───────────────────────┘  (only!)  │ /ws/signaling (SDP/ICE)   │
                                        └─────────▲────────────────┘
   Browser SPA (CC webui)                         │ WebRTC media
   ┌───────────────────────┐                      │ (smallwebrtc)
   │ /ws/voice-test (PCM)   │      getUserMedia ───┘ browser peer
   └───────────────────────┘
```

CC and dograh **share no audio stream today.** Their only contact surface is the
REST client. The two places audio exists — CC's PyAudio loop and dograh's
browser WebRTC peer — are on different sides of the boundary and never meet.

### 1d. Prior art: the voice-test WS (relevant, but not a bridge)

The new `/ws/voice-test` work (`web/routes/voice_test.py`,
`app/voice_test_pipeline.py`) **does** stream *browser* audio to a CC pipeline:
binary PCM/webm frames are buffered (`voice_test.py:126`,
`voice_test_pipeline.py:207`) and run through the same wakeword→transcript→match
shape (`voice_test_pipeline.py:256`). This proves CC can be an *audio sink for
browser audio over a WS*. But note:

- It is **dry-run only** — actions are described, never executed
  (`voice_test_pipeline.py:144`, `:264`–`:281`); `dry_run:false` is rejected
  (`voice_test.py:84`).
- It is **one-directional ingest**; CC produces no outbound audio track.
- It shares no stream with dograh — it's a parallel consumer of the *same
  browser mic* at best, not a bridge to dograh's peer.

This is the real groundwork the ROADMAP refers to (`ROADMAP.md:120`): browser →
CC audio transport exists. dograh ↔ CC audio transport does not.

---

## 2. The core technical problem

Two **independent audio consumers** want the same input:
1. CC's wakeword detector (needs raw 16 kHz PCM frames, locally).
2. dograh's pipecat pipeline (needs a WebRTC media track, in its container).

A "shared stream" means one capture feeds both, *and* a wakeword hit during a
live dograh call can interrupt (barge-in) and hand off. Four options:

**(a) CC as audio source feeding dograh via WebRTC.** CC's Python process becomes
a WebRTC peer (e.g. `aiortc`) that publishes the mic track to dograh's
`smallwebrtc` endpoint, while *also* tapping the same PCM for openwakeword.
Feasibility: **medium-low.** It removes the browser from the media path (good for
a local-first assistant), reuses CC's existing PCM capture (`wakeword.py:127`),
and keeps wakeword in-process where it already works. BUT it requires (i) a new
heavy dep (`aiortc`), (ii) that dograh's `smallwebrtc` peer will accept an
external/non-browser offerer on `/ws/signaling` — **unverified**, and (iii)
re-encoding PCM→Opus. This is the most architecturally "honest" option for
local-first but the most build-heavy.

**(b) Shared SFU / mixer.** Stand up an SFU (LiveKit/mediasoup) that both CC and
dograh subscribe to. Feasibility: **low / overkill.** Adds a whole new
infrastructure component and a second container, for a single-user local
assistant. dograh's `smallwebrtc` is explicitly the *no-infrastructure* path
(`dograh_webcall_loopback.spec.ts:5`); bolting an SFU on top defeats its purpose.
See §6.

**(c) Browser-side shared capture.** The browser captures the mic once
(`getUserMedia`) and tees it to *both* CC's `/ws/voice-test` WS *and* dograh's
`smallwebrtc` peer. Feasibility: **medium, and closest to existing code.** The
voice-test WS already ingests browser PCM (`voice_test.py:126`), and dograh's
call leg already lives in the browser (`dograh_webcall_loopback.spec.ts:7`). A
`MediaStreamTrack` can be cloned/fanned to a WS (PCM) and an `RTCPeerConnection`
simultaneously. Wakeword detection runs server-side in CC; on a hit, CC tells the
browser (over `/ws`) to mute/duck the dograh peer or signals dograh to interrupt.
Downside: only works when a browser tab is the audio origin — it does **not**
cover the headless/local-only assistant use case, and it splits the wakeword
logic (CC) from the call media (browser↔dograh) across the network, adding
latency to the barge-in decision.

**(d) Barge-in via dograh's own VAD/interrupt.** Don't bridge audio at all; let
dograh's pipecat VAD handle interruptions natively (pipecat has built-in
interruption support), and use CC only for *state* and *initiation*. Feasibility:
**high for "interrupt the bot mid-utterance"**, but it does **not** satisfy the
literal ROADMAP goal of *CC's wakeword* triggering the handoff
(`ROADMAP.md:127`). It's the pragmatic answer if "barge-in" means "user can talk
over the agent," and it needs zero new CC audio plumbing. Worth calling out as
the cheapest path to the *user-visible* benefit.

**Architecture reality check.** CC = Python in-process + a browser SPA; dograh =
separate container whose call leg is a browser peer. Options (a) and (c) are the
only ones that put a *real shared stream* in reach without new infra; (a) suits
local-first, (c) suits the webapp. (b) is overkill; (d) sidesteps the literal
goal but delivers most of the value.

---

## 3. Bidirectional state design

### 3a. dograh run state → CC `StateManager` (inbound)

What exists: `get_workflow_run(workflow_id, run_id)` (`dograh_client.py:221`) and
`list_workflow_runs` (`dograh_client.py:202`) return a run record. The loopback
roadmap already reads run transcripts this way (`ROADMAP.md:109`). So **polling
run state is possible today** with the existing client.

What's missing / unknown: the **exact field** in the run record that encodes
`ringing`/`in-call`/`ended`, and whether dograh exposes a **push channel**
(webhook or events WS) so CC doesn't have to poll. The only push surface we have
evidence of is `/ws/signaling` (`dograh_webcall_loopback.spec.ts:75`), which
carries SDP/ICE for the browser peer — **not** an application-level call-state
feed. **No webhook or event-stream method exists in `DograhClient`** today
(`dograh_client.py` has only the REST methods listed in §1b). → polling is the
safe assumption; an event channel is an unverified hope.

Wiring on the CC side is ready: a poller maps dograh state to a CC state via
`StateManager.change_state("<state>")` (`state_manager.py:117`), and that already
fans out to the UI — `WebModeServer` registers `_on_state_change` as a state
callback (`web_mode.py:431`) which broadcasts a `state_change` WS message
(`web_mode.py:936`–`:951`). CC's canonical states are `idle`/`chatty`/`computer`
(`state_manager.py:43`, config-driven `state_models`); a dograh call would map to
`chatty` (or a new `in_call` state added to config) with `ended`→`idle`.

### 3b. CC mode → dograh session metadata (outbound)

ROADMAP wants CC's `chatty`/`computer` mode published into dograh's session
metadata (`ROADMAP.md:128`). **No `DograhClient` method does this** — there is no
"update session metadata" or "set run context" call in `dograh_client.py`. The
closest write surfaces are `create_workflow_run` (`dograh_client.py:180`, accepts
only `mode`/`name`) and `initiate_call` (`dograh_client.py:155`). So today CC
could only stamp mode **at run-creation time** by passing it in `name` (a hack)
or, if dograh's run-create accepts a metadata/context object, via that field —
**unverified which, if any, dograh exposes.** Mid-call mode updates would need a
dograh API that we have no evidence exists. → **outbound state is blocked on an
unknown/absent dograh API.**

---

## 4. Honest feasibility verdict per option

| Option | Feasible in THIS architecture? | Biggest risk / unknown |
|---|---|---|
| (a) CC as WebRTC source to dograh | Possible, build-heavy | Does dograh `smallwebrtc` accept a non-browser external offerer? (unverified) + new `aiortc` dep + Opus encode |
| (b) SFU/mixer | No (overkill) | New infra/container for a single-user local app; defeats `smallwebrtc`'s no-infra premise |
| (c) Browser-shared capture | Yes, for the webapp case | Splits wakeword (CC) from media (browser↔dograh) across the net → barge-in latency; doesn't cover headless/local-only |
| (d) dograh-native VAD interrupt | Yes, cheapest | Doesn't satisfy the literal "CC wakeword triggers handoff" goal |

Cross-cutting risks / things to verify against a **live dograh instance**:

1. **Event stream vs. polling.** Does dograh emit call-state events (webhook /
   events WS), or must CC poll `get_workflow_run`? Polling adds latency and load;
   it's the only thing the current client supports.
2. **External audio track ingest.** Can dograh's `smallwebrtc` peer accept an
   audio track from a non-browser WebRTC offerer (CC's Python `aiortc` peer)?
   The loopback spec only ever drives it from Chromium
   (`dograh_webcall_loopback.spec.ts:52`–`:61`).
3. **Session-metadata write API.** Is there any dograh endpoint to attach/update
   per-session metadata mid-call? Not in `DograhClient`; existence unknown.
4. **Wakeword→handoff latency.** openwakeword runs at 80 ms chunks
   (`wakeword.py:58`); add transcription + a network hop to dograh + WebRTC
   renegotiation — end-to-end barge-in latency is unmeasured and could feel slow.
5. **Provider prerequisites.** dograh's audio path needs STT/TTS/LLM wired; the
   OSS image points them at dograh's hosted cloud and the loopback is "blocked at
   LLM config" until configured (`ROADMAP.md:101`, `:105`). **No shared-audio
   barge-in can be demonstrated end-to-end until those providers are wired.**

---

## 5. Recommended phased plan (smallest-viable-first)

**P-WB0 — State-only bridge (buildable now, no shared audio).**
- Add a dograh run-state poller (out-of-process task or a small adapter) that
  calls `get_workflow_run` (`dograh_client.py:221`) on an active run and maps
  `ringing`/`in-call`/`ended` → a CC state via `change_state`
  (`state_manager.py:117`). Reuse the existing `/ws` `state_change` broadcast
  (`web_mode.py:936`) so the UI badge reflects call state with zero new transport.
- Deliverable: CC dashboard shows "in dograh call" / returns to `idle` on end.
- Blockers: only needs the *field name* for run state confirmed against a live
  instance (§4.1). Everything else exists.

**P-WB1 — Outbound mode stamp at run creation (cheap, partial).**
- If dograh's run-create accepts a metadata/context object, pass CC's current
  mode at `create_workflow_run`/`initiate_call` time. If not, defer — do **not**
  hack it into `name`. Verify the API first (§4.3).

**P-WB2 — dograh-native barge-in (option d) for the webapp call.**
- Lean on pipecat's built-in interruption so a user can talk over the agent
  during a browser `smallwebrtc` call. No CC audio plumbing. Delivers the
  user-visible "barge-in" benefit without the shared-stream build.

**P-WB3 — Browser-shared capture (option c), webapp only.**
- Tee the browser mic to both `/ws/voice-test` (CC wakeword, server-side) and the
  dograh `smallwebrtc` peer; on a CC wakeword hit, signal the browser to duck/mute
  the dograh peer or send dograh an interrupt. Blocked on: §4.2/§4.4 latency, and
  providers wired (§4.5). Build only after P-WB2 proves the call path end-to-end.

**P-WB4 — CC as native WebRTC source (option a), local-first.**
- Only if a headless/local barge-in (no browser) is a real requirement. Adds
  `aiortc` + Opus and depends on §4.2 being a confirmed "yes". Largest effort,
  smallest incremental audience. Treat as research, not committed work.

**E2E test (`ROADMAP.md:129`)** — wake-word → call → live audio → end → `idle`
is only meaningful after P-WB2/P-WB3 *and* providers are configured
(`ROADMAP.md:101`). Until then, the testable slice is P-WB0's state reflection,
which can be unit/integration tested against a mocked `DograhClient`.

---

## 6. What is OVERKILL / premature for a local-first assistant

- **An SFU/mixer (option b).** A LiveKit/mediasoup deployment for a single-user
  desktop assistant is disproportionate infrastructure; `smallwebrtc` exists
  precisely to avoid it (`dograh_webcall_loopback.spec.ts:5`).
- **CC-as-WebRTC-peer (P-WB4) before there's a headless requirement.** Adding
  `aiortc` + Opus encoding to satisfy a use case (local barge-in with no browser)
  that may never be exercised is premature. The browser-shared path (P-WB3)
  covers the realistic webapp scenario with far less new code.
- **Building outbound session-metadata sync before confirming the API exists
  (§3b/§4.3).** Designing a mid-call mode-push protocol against a dograh
  capability we have no evidence of is speculative.
- **Any shared-audio work before STT/TTS/LLM providers are wired**
  (`ROADMAP.md:101`). The audio bridge has nothing to hand off *to* until
  dograh's pipeline can actually run a call; sequence the telephony/provider
  roadmap items first.
- **Splitting wakeword across the network when local already works.** CC's
  in-process openwakeword loop (`wakeword.py:172`) is the low-latency path;
  routing audio out to bridge it should be justified by a concrete cross-process
  need, not pursued for architectural symmetry.

**Bottom line:** ship P-WB0 (state bridge) now for real, visible value; treat the
shared-audio barge-in as research gated on live-instance verification (§4) and
the provider prerequisites (`ROADMAP.md:101`).
