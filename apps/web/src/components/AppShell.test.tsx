import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import "@/i18n";
import { AppShell } from "./AppShell";

describe("AppShell mobile navigation", () => {
  it("opens from the hamburger button and closes after navigation", async () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<p>Home</p>} />
            <Route path="profile" element={<p>Profile</p>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    const menuButton = screen.getByRole("button", { name: "Open navigation" });
    const navigation = screen.getByRole("navigation", { name: "Primary navigation" });
    expect(menuButton).toHaveAttribute("aria-expanded", "false");
    expect(navigation).toHaveAttribute("data-open", "false");

    fireEvent.click(menuButton);
    expect(menuButton).toHaveAttribute("aria-expanded", "true");
    expect(navigation).toHaveAttribute("data-open", "true");

    fireEvent.click(screen.getByRole("link", { name: "Life profile" }));
    await waitFor(() => expect(menuButton).toHaveAttribute("aria-expanded", "false"));
    expect(screen.getByText("Profile")).toBeInTheDocument();
  });
});
