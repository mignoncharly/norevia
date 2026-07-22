import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import "@/i18n";
import { detectMobilePlatform, PwaInstallPrompt } from "./PwaInstallPrompt";

const originalNavigator = {
  userAgent: navigator.userAgent,
  platform: navigator.platform,
  maxTouchPoints: navigator.maxTouchPoints,
};

function emulateDevice(userAgent: string, platform: string, maxTouchPoints: number): void {
  Object.defineProperty(navigator, "userAgent", { configurable: true, value: userAgent });
  Object.defineProperty(navigator, "platform", { configurable: true, value: platform });
  Object.defineProperty(navigator, "maxTouchPoints", { configurable: true, value: maxTouchPoints });
  vi.stubGlobal("matchMedia", vi.fn(() => ({
    matches: false,
    media: "(display-mode: standalone)",
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })));
}

afterEach(() => {
  cleanup();
  emulateDevice(originalNavigator.userAgent, originalNavigator.platform, originalNavigator.maxTouchPoints);
  window.localStorage.clear();
  vi.unstubAllGlobals();
});

describe("detectMobilePlatform", () => {
  it("detects Android devices", () => {
    expect(detectMobilePlatform("Mozilla/5.0 (Linux; Android 15; Pixel 9)", "Linux armv8l", 5)).toBe("android");
  });

  it("detects iPhone, iPad, and iPadOS desktop user agents", () => {
    expect(detectMobilePlatform("Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X)", "iPhone", 5)).toBe("ios");
    expect(detectMobilePlatform("Mozilla/5.0 (Macintosh; Intel Mac OS X)", "MacIntel", 5)).toBe("ios");
  });

  it("does not prompt ordinary desktop browsers", () => {
    expect(detectMobilePlatform("Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Win32", 0)).toBeNull();
  });
});

describe("PwaInstallPrompt", () => {
  it("shows Apple Home Screen instructions on iPhone and iPad", async () => {
    emulateDevice("Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X)", "iPhone", 5);
    render(<PwaInstallPrompt />);
    expect(await screen.findByRole("dialog", { name: "Install Norevia" })).toBeInTheDocument();
    expect(screen.getByText(/Tap Share, then choose Add to Home Screen/)).toBeInTheDocument();
  });

  it("shows browser-menu installation instructions on Android without a native prompt", async () => {
    emulateDevice("Mozilla/5.0 (Linux; Android 15; Pixel 9)", "Linux armv8l", 5);
    render(<PwaInstallPrompt />);
    expect(await screen.findByRole("dialog", { name: "Install Norevia" })).toBeInTheDocument();
    expect(screen.getByText(/Open your browser menu/)).toBeInTheDocument();
  });
});
