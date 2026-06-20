import { renderHook } from "@testing-library/react";
import { afterEach, describe, expect, test } from "vitest";
import {
  __resetUnsavedChanges,
  hasUnsavedChanges,
  subscribeUnsavedChanges,
  useUnsavedChanges,
} from "./useUnsavedChanges";

afterEach(() => {
  __resetUnsavedChanges();
});

describe("useUnsavedChanges", () => {
  test("does not register while clean", () => {
    renderHook(() => useUnsavedChanges(false));
    expect(hasUnsavedChanges()).toBe(false);
  });

  test("registers while dirty and unregisters when it goes clean", () => {
    const { rerender } = renderHook(
      ({ dirty }: { dirty: boolean }) => useUnsavedChanges(dirty),
      { initialProps: { dirty: false } },
    );
    expect(hasUnsavedChanges()).toBe(false);

    rerender({ dirty: true });
    expect(hasUnsavedChanges()).toBe(true);

    rerender({ dirty: false });
    expect(hasUnsavedChanges()).toBe(false);
  });

  test("unregisters on unmount", () => {
    const { unmount } = renderHook(() => useUnsavedChanges(true));
    expect(hasUnsavedChanges()).toBe(true);
    unmount();
    expect(hasUnsavedChanges()).toBe(false);
  });

  test("stays dirty while any one of several forms is dirty", () => {
    const a = renderHook(() => useUnsavedChanges(true));
    const b = renderHook(() => useUnsavedChanges(true));
    expect(hasUnsavedChanges()).toBe(true);

    a.unmount();
    // Still dirty: the second form is registered.
    expect(hasUnsavedChanges()).toBe(true);

    b.unmount();
    expect(hasUnsavedChanges()).toBe(false);
  });

  test("notifies subscribers on registration changes", () => {
    let notifications = 0;
    const unsubscribe = subscribeUnsavedChanges(() => {
      notifications += 1;
    });

    const { rerender, unmount } = renderHook(
      ({ dirty }: { dirty: boolean }) => useUnsavedChanges(dirty),
      { initialProps: { dirty: false } },
    );
    rerender({ dirty: true });
    expect(notifications).toBeGreaterThan(0);

    const after = notifications;
    unmount();
    expect(notifications).toBeGreaterThan(after);

    unsubscribe();
  });
});
