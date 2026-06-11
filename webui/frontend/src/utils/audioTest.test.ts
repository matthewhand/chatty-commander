import { vi } from "vitest";
import { playTestTone, rmsLevel, runMicTest } from "./audioTest";

// ─── Web Audio fakes ──────────────────────────────────────────────────────────
// jsdom ships neither AudioContext nor getUserMedia, so each test installs
// exactly the surface area the utility touches.

let analyserFill = 128; // 128 == silence in byte time-domain data

class FakeAnalyser {
  fftSize = 2048;
  frequencyBinCount = 128;
  getByteTimeDomainData(buffer: Uint8Array) {
    buffer.fill(analyserFill);
  }
}

let oscillatorEmitsEnded = true;

class FakeOscillator {
  type = "sine";
  frequency = { value: 0 };
  onended: (() => void) | null = null;
  connect = vi.fn();
  start = vi.fn();
  stop = vi.fn(() => {
    if (oscillatorEmitsEnded) this.onended?.();
  });
}

class FakeGainNode {
  gain = {
    setValueAtTime: vi.fn(),
    linearRampToValueAtTime: vi.fn(),
  };
  connect = vi.fn();
}

class FakeAudioContext {
  static instances: FakeAudioContext[] = [];
  currentTime = 0;
  destination = {};
  closed = false;
  lastOscillator: FakeOscillator | null = null;

  constructor() {
    FakeAudioContext.instances.push(this);
  }

  createMediaStreamSource = vi.fn(() => ({ connect: vi.fn() }));
  createAnalyser = vi.fn(() => new FakeAnalyser());
  createOscillator = vi.fn(() => {
    this.lastOscillator = new FakeOscillator();
    return this.lastOscillator;
  });
  createGain = vi.fn(() => new FakeGainNode());
  close = vi.fn(async () => {
    this.closed = true;
  });
}

const fakeTrack = { stop: vi.fn() };
const fakeStream = { getTracks: () => [fakeTrack] } as unknown as MediaStream;

const installMediaDevices = (getUserMedia: unknown) => {
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: getUserMedia ? { getUserMedia } : undefined,
  });
};

beforeEach(() => {
  analyserFill = 128;
  FakeAudioContext.instances = [];
  fakeTrack.stop.mockClear();
  (window as unknown as { AudioContext?: unknown }).AudioContext = FakeAudioContext;
  installMediaDevices(vi.fn().mockResolvedValue(fakeStream));
});

afterEach(() => {
  vi.useRealTimers();
  delete (window as unknown as { AudioContext?: unknown }).AudioContext;
});

// ─── rmsLevel ─────────────────────────────────────────────────────────────────
describe("rmsLevel", () => {
  test("returns 0 for silence and for an empty buffer", () => {
    expect(rmsLevel(new Uint8Array(0))).toBe(0);
    expect(rmsLevel(new Uint8Array(64).fill(128))).toBe(0);
  });

  test("scales with amplitude and caps at 100", () => {
    // (160 - 128) / 128 = 0.25 RMS -> 0.25 * 300 = 75
    expect(rmsLevel(new Uint8Array(64).fill(160))).toBe(75);
    // Full-scale signal would exceed 100; it is clamped.
    expect(rmsLevel(new Uint8Array(64).fill(255))).toBe(100);
  });
});

// ─── runMicTest ───────────────────────────────────────────────────────────────
describe("runMicTest", () => {
  test("samples levels, reports them, and resolves with the peak", async () => {
    vi.useFakeTimers({
      toFake: ["setTimeout", "clearTimeout", "requestAnimationFrame", "cancelAnimationFrame"],
    });
    analyserFill = 160; // -> level 75
    const onLevel = vi.fn();

    const promise = runMicTest({ durationMs: 500, onLevel });
    await vi.advanceTimersByTimeAsync(600);
    const result = await promise;

    expect(result.peakLevel).toBe(75);
    expect(onLevel).toHaveBeenCalledWith(75);
    // Cleanup: stream released, context closed.
    expect(fakeTrack.stop).toHaveBeenCalled();
    expect(FakeAudioContext.instances).toHaveLength(1);
    expect(FakeAudioContext.instances[0].closed).toBe(true);
  });

  test("resolves with peak 0 when the input is silent", async () => {
    vi.useFakeTimers({
      toFake: ["setTimeout", "clearTimeout", "requestAnimationFrame", "cancelAnimationFrame"],
    });
    analyserFill = 128;

    const promise = runMicTest({ durationMs: 200 });
    await vi.advanceTimersByTimeAsync(300);

    await expect(promise).resolves.toEqual({ peakLevel: 0 });
  });

  test("rejects when getUserMedia is unavailable", async () => {
    installMediaDevices(undefined);
    await expect(runMicTest()).rejects.toThrow(/not supported/i);
  });

  test("rejects when Web Audio is unavailable, without requesting the mic", async () => {
    delete (window as unknown as { AudioContext?: unknown }).AudioContext;
    const getUserMedia = vi.fn();
    installMediaDevices(getUserMedia);

    await expect(runMicTest()).rejects.toThrow(/web audio/i);
    expect(getUserMedia).not.toHaveBeenCalled();
  });

  test("propagates permission denial from getUserMedia", async () => {
    installMediaDevices(vi.fn().mockRejectedValue(new Error("Permission denied")));
    await expect(runMicTest()).rejects.toThrow("Permission denied");
  });
});

// ─── playTestTone ─────────────────────────────────────────────────────────────
describe("playTestTone", () => {
  test("plays a sine tone and resolves when it ends", async () => {
    await playTestTone({ durationMs: 1000, frequency: 440 });

    expect(FakeAudioContext.instances).toHaveLength(1);
    const ctx = FakeAudioContext.instances[0];
    const osc = ctx.lastOscillator!;
    expect(osc.type).toBe("sine");
    expect(osc.frequency.value).toBe(440);
    expect(osc.start).toHaveBeenCalled();
    expect(osc.stop).toHaveBeenCalledWith(1); // currentTime 0 + 1s
    expect(ctx.closed).toBe(true);
  });

  test("falls back to a timeout when onended never fires", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    oscillatorEmitsEnded = false; // stop() will not emit onended

    try {
      const promise = playTestTone({ durationMs: 300 });
      await vi.advanceTimersByTimeAsync(600); // 300ms tone + 250ms grace
      await expect(promise).resolves.toBeUndefined();
      expect(FakeAudioContext.instances[0].closed).toBe(true);
    } finally {
      oscillatorEmitsEnded = true;
    }
  });

  test("rejects when Web Audio is unavailable", async () => {
    delete (window as unknown as { AudioContext?: unknown }).AudioContext;
    await expect(playTestTone()).rejects.toThrow(/web audio/i);
  });
});
