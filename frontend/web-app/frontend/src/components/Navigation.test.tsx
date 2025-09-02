import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import Navigation from "./Navigation";

// Mock the useAuth hook
const mockLogout = jest.fn();
jest.mock("../hooks/useAuth", () => ({
  useAuth: () => ({
    user: { username: "testuser" },
    logout: mockLogout,
    isAuthenticated: true,
  }),
}));

const renderNavigation = () => {
  return render(
    <BrowserRouter>
      <Navigation />
    </BrowserRouter>,
  );
};

describe("Navigation Component", () => {
  test("renders navigation links", () => {
    renderNavigation();

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Configuration")).toBeInTheDocument();
    expect(screen.getByText("Audio Settings")).toBeInTheDocument();
  });

  test("renders logout button", () => {
    renderNavigation();

    expect(screen.getByText("Logout")).toBeInTheDocument();
  });

  test("calls logout when logout button is clicked", () => {
    renderNavigation();

    fireEvent.click(screen.getByText("Logout"));
    expect(mockLogout).toHaveBeenCalled();
  });

  beforeEach(() => {
    mockLogout.mockClear();
  });
});
