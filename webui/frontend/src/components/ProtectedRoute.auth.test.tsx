import { vi, test, expect } from "vitest";
import React from "react";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";

vi.mock("../hooks/useAuth", () => ({
  useAuth: () => ({ isAuthenticated: true }),
}));

test("renders children when authenticated", () => {
  const { container } = render(
    <MemoryRouter initialEntries={["/secret"]}>
      <ProtectedRoute>
        <div>Secret</div>
      </ProtectedRoute>
    </MemoryRouter>,
  );
  expect(container.textContent).toContain("Secret");
});
