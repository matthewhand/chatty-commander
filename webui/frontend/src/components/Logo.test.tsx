import React from "react";
import { render, screen } from "@testing-library/react";
import Logo from "./Logo";

describe("Logo", () => {
  test("renders the unified 'ChattyCommander' wordmark and an accessible name", () => {
    render(<Logo />);
    // Single accessible image labelled with the unified brand name.
    expect(screen.getByRole("img", { name: "ChattyCommander" })).toBeInTheDocument();
    // Wordmark is split into Chatty + Commander spans but reads as one name.
    expect(screen.getByText("Chatty")).toBeInTheDocument();
    expect(screen.getByText("Commander")).toBeInTheDocument();
  });

  test("iconOnly hides the wordmark text", () => {
    render(<Logo iconOnly />);
    expect(screen.queryByText("Chatty")).not.toBeInTheDocument();
    expect(screen.queryByText("Commander")).not.toBeInTheDocument();
  });

  test("decorative removes the role/label so it is hidden from assistive tech", () => {
    render(<Logo decorative iconOnly />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(document.querySelector("span")).toHaveAttribute("aria-hidden", "true"); // eslint-disable-line testing-library/no-node-access
  });

  test("mark strokes with currentColor so it is themeable", () => {
    render(<Logo iconClassName="text-secondary" />);
    const svg = document.querySelector("svg"); // eslint-disable-line testing-library/no-node-access
    expect(svg).toHaveAttribute("stroke", "currentColor");
    expect(svg?.getAttribute("class")).toContain("text-secondary");
  });
});
