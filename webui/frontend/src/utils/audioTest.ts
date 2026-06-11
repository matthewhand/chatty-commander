/**
 * In-browser audio device tests.
 *
 * These run entirely client-side via getUserMedia + Web Audio — the server
 * never claims to have exercised hardware it can't see. The microphone test
 * mirrors the AnalyserNode level-meter approach used by VoiceTestPage; the
 * output test plays a short generated tone through an OscillatorNode.
 *
 * Note: both tests use the browser's currently selected default devices.
 * Server-side device selection (sounddevice indices) is configured
 * separately and applied on save.
 */

export interface MicTestOptions {
  /** How long to sample the microphone, in milliseconds. */
  durationMs?: number;
  /** Called with the current input level (0-100) on every animation frame. */
  onLevel?: (level: number) => void;
}

export interface MicTestResult {
  /** Peak RMS-derived input level observed during the test, scaled 0-100. */
  peakLevel: number;
}

export interface ToneTestOptions {
  /** Tone duration in milliseconds. */
  durationMs?: number;
  /** Tone frequency in Hz. */
  frequency?: number;
  /** Peak gain (0-1); kept low so the test isn't startling. */
  gain?: number;
}

type AudioContextCtor = typeof AudioContext;

function getAudioContextCtor(): AudioContextCtor | undefined {
  return (
    window.AudioContext ||
    (window as unknown as { webkitAudioContext?: AudioContextCtor }).webkitAudioContext
  );
}

/** Convert a time-domain byte buffer to an RMS level scaled to 0-100. */
export function rmsLevel(buffer: Uint8Array): number {
  if (buffer.length === 0) return 0;
  let sum = 0;
  for (let i = 0; i < buffer.length; i++) {
    const v = (buffer[i] - 128) / 128;
    sum += v * v;
  }
  return Math.min(100, Math.round(Math.sqrt(sum / buffer.length) * 300));
}

/**
 * Request microphone access and measure the input level for `durationMs`.
 *
 * Resolves with the peak level seen; rejects if the browser lacks the
 * required APIs or the user denies permission. Always releases the stream
 * and closes the AudioContext when done.
 */
export async function runMicTest(options: MicTestOptions = {}): Promise<MicTestResult> {
  const { durationMs = 3000, onLevel } = options;

  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("Microphone access is not supported in this browser.");
  }
  const AudioCtx = getAudioContextCtor();
  if (!AudioCtx) {
    throw new Error("Web Audio is not supported in this browser.");
  }

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

  let ctx: AudioContext | null = null;
  let rafId: number | null = null;
  let timerId: ReturnType<typeof setTimeout> | null = null;
  let peak = 0;

  try {
    ctx = new AudioCtx();
    const source = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    const buffer = new Uint8Array(analyser.frequencyBinCount);

    await new Promise<void>((resolve) => {
      timerId = setTimeout(resolve, durationMs);
      const tick = () => {
        analyser.getByteTimeDomainData(buffer);
        const level = rmsLevel(buffer);
        peak = Math.max(peak, level);
        onLevel?.(level);
        rafId = requestAnimationFrame(tick);
      };
      rafId = requestAnimationFrame(tick);
    });
  } finally {
    if (rafId !== null) cancelAnimationFrame(rafId);
    if (timerId !== null) clearTimeout(timerId);
    try {
      await ctx?.close();
    } catch {
      /* already closed */
    }
    stream.getTracks().forEach((t) => t.stop());
  }

  return { peakLevel: peak };
}

/**
 * Play a short generated sine tone through the browser's default output.
 *
 * Uses a gentle gain envelope to avoid clicks. Resolves when the tone ends
 * (with a small timeout fallback in case `onended` never fires); rejects if
 * Web Audio is unavailable.
 */
export async function playTestTone(options: ToneTestOptions = {}): Promise<void> {
  const { durationMs = 1500, frequency = 440, gain = 0.25 } = options;

  const AudioCtx = getAudioContextCtor();
  if (!AudioCtx) {
    throw new Error("Web Audio is not supported in this browser.");
  }

  const ctx = new AudioCtx();
  try {
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    const now = ctx.currentTime;
    const durS = durationMs / 1000;

    oscillator.type = "sine";
    oscillator.frequency.value = frequency;
    // Ramp in/out so the tone starts and ends without clicks.
    gainNode.gain.setValueAtTime(0, now);
    gainNode.gain.linearRampToValueAtTime(gain, now + 0.05);
    gainNode.gain.setValueAtTime(gain, now + Math.max(0.05, durS - 0.1));
    gainNode.gain.linearRampToValueAtTime(0, now + durS);

    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);

    await new Promise<void>((resolve) => {
      let settled = false;
      const finish = () => {
        if (settled) return;
        settled = true;
        clearTimeout(fallback);
        resolve();
      };
      // Fallback in case onended never fires (seen in some WebAudio shims).
      const fallback = setTimeout(finish, durationMs + 250);
      oscillator.onended = finish;
      oscillator.start(now);
      oscillator.stop(now + durS);
    });
  } finally {
    try {
      await ctx.close();
    } catch {
      /* already closed */
    }
  }
}
