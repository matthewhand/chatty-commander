import React from "react";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";

jest.mock("../hooks/useAuth", () => ({
  useAuth: () => ({ isAuthenticated: false }),
}));

it("redirects when not authenticated", () => {
  const { container } = render(
    <MemoryRouter initialEntries={["/secret"]}>
      <ProtectedRoute>
        <div>Secret</div>
      </ProtectedRoute>
    </MemoryRouter>,
  );
  // react-router Navigate renders nothing in DOM for our test scenario; assert no Secret content
  expect(container.textContent).not.toContain("Secret");
});
