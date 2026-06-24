import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import ScrollToTop from "./ScrollToTop";

/**
 * Renders ScrollToTop alongside a stand-in for the app's scrolling <main>
 * container. The button must observe THAT element's scroll, not window scroll,
 * because the real layout scrolls inside `<main class="overflow-y-auto">`.
 */
function renderWithMain(target: string = "#main-content") {
  return render(
    <>
      <main id="main-content" />
      <ScrollToTop target={target} />
    </>,
  );
}

describe("ScrollToTop", () => {
  test("stays hidden until the main container is scrolled past the threshold", () => {
    renderWithMain();
    const button = screen.getByRole("button", { name: /scroll to top/i });
    // Hidden initially (opacity-0 + pointer-events-none).
    expect(button.className).toContain("opacity-0");
    expect(button.className).toContain("pointer-events-none");
  });

  test("becomes visible when the <main> element scrolls down", () => {
    renderWithMain();
    const main = screen.getByRole("main");
    const button = screen.getByRole("button", { name: /scroll to top/i });

    // Simulate scrolling the main container (not the window).
    Object.defineProperty(main, "scrollTop", { value: 500, configurable: true });
    fireEvent.scroll(main);

    expect(button.className).toContain("opacity-100");
    expect(button.className).not.toContain("pointer-events-none");
  });

  test("hides again when scrolled back near the top", () => {
    renderWithMain();
    const main = screen.getByRole("main");
    const button = screen.getByRole("button", { name: /scroll to top/i });

    Object.defineProperty(main, "scrollTop", {
      value: 500,
      configurable: true,
    });
    fireEvent.scroll(main);
    expect(button.className).toContain("opacity-100");

    Object.defineProperty(main, "scrollTop", { value: 0, configurable: true });
    fireEvent.scroll(main);
    expect(button.className).toContain("opacity-0");
  });

  test("clicking scrolls the <main> element to the top", () => {
    renderWithMain();
    const main = screen.getByRole("main");
    const scrollToSpy = vi.fn();
    main.scrollTo = scrollToSpy as unknown as typeof main.scrollTo;

    Object.defineProperty(main, "scrollTop", {
      value: 500,
      configurable: true,
    });
    fireEvent.scroll(main);

    fireEvent.click(screen.getByRole("button", { name: /scroll to top/i }));
    expect(scrollToSpy).toHaveBeenCalledWith({ top: 0, behavior: "smooth" });
  });
});
