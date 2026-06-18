import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { DynamicDropdown } from "./DynamicDropdown";

function renderDropdown() {
  return render(
    <DynamicDropdown buttonContent="Menu" ariaLabel="Open options">
      <li>
        <a href="#first">First</a>
      </li>
      <li>
        <button type="button">Second</button>
      </li>
      <li>
        <button type="button">Third</button>
      </li>
    </DynamicDropdown>,
  );
}

describe("DynamicDropdown", () => {
  it("opens on click and exposes menu semantics", async () => {
    renderDropdown();
    const trigger = screen.getByRole("button", { name: /open options/i });
    expect(trigger).toHaveAttribute("aria-haspopup", "menu");
    expect(trigger).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(trigger);

    const menu = await screen.findByRole("menu");
    expect(menu).toBeInTheDocument();
    expect(trigger).toHaveAttribute("aria-expanded", "true");

    const items = screen.getAllByRole("menuitem");
    expect(items).toHaveLength(3);
  });

  it("focuses the first item on open", async () => {
    renderDropdown();
    fireEvent.click(screen.getByRole("button", { name: /open options/i }));
    await waitFor(() =>
      expect(screen.getByText("First")).toHaveFocus(),
    );
  });

  it("moves focus with arrow keys (roving focus)", async () => {
    renderDropdown();
    fireEvent.click(screen.getByRole("button", { name: /open options/i }));
    const menu = await screen.findByRole("menu");
    await waitFor(() => expect(screen.getByText("First")).toHaveFocus());

    fireEvent.keyDown(menu, { key: "ArrowDown" });
    expect(screen.getByText("Second")).toHaveFocus();

    fireEvent.keyDown(menu, { key: "ArrowDown" });
    expect(screen.getByText("Third")).toHaveFocus();

    // Wraps around to the first item.
    fireEvent.keyDown(menu, { key: "ArrowDown" });
    expect(screen.getByText("First")).toHaveFocus();

    // ArrowUp wraps back to the last.
    fireEvent.keyDown(menu, { key: "ArrowUp" });
    expect(screen.getByText("Third")).toHaveFocus();
  });

  it("closes on Escape and restores focus to the trigger", async () => {
    renderDropdown();
    const trigger = screen.getByRole("button", { name: /open options/i });
    fireEvent.click(trigger);
    const menu = await screen.findByRole("menu");

    fireEvent.keyDown(menu, { key: "Escape" });

    await waitFor(() =>
      expect(screen.queryByRole("menu")).not.toBeInTheDocument(),
    );
    expect(trigger).toHaveFocus();
    expect(trigger).toHaveAttribute("aria-expanded", "false");
  });

  it("closes on outside click", async () => {
    render(
      <div>
        <DynamicDropdown buttonContent="Menu" ariaLabel="Open options">
          <li>
            <a href="#x">First</a>
          </li>
        </DynamicDropdown>
        <span data-testid="outside">outside</span>
      </div>,
    );
    fireEvent.click(screen.getByRole("button", { name: /open options/i }));
    expect(await screen.findByRole("menu")).toBeInTheDocument();

    fireEvent.mouseDown(screen.getByTestId("outside"));

    await waitFor(() =>
      expect(screen.queryByRole("menu")).not.toBeInTheDocument(),
    );
  });

  it("opens via ArrowDown on the trigger", async () => {
    renderDropdown();
    const trigger = screen.getByRole("button", { name: /open options/i });
    fireEvent.keyDown(trigger, { key: "ArrowDown" });
    expect(await screen.findByRole("menu")).toBeInTheDocument();
  });
});
