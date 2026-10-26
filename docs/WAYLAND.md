# Wayland (beta)

Wayland does not allow the same global capture and always-on-top overlay as
X11. Spectra's Wayland mode is **pragmatic**:

- capture via **XDG Desktop Portal** (Screenshot) or a compositor tool;
- trigger scans from the **tray** or `spectra-hud --scan` bound to a system
  shortcut;
- show results in a normal **Results** window, not anchored cards;
- follow-up questions from the Results window.

The X11 mode keeps the full anchored overlay.

## Capture backends

Try in this order:

1. `org.freedesktop.portal.Screenshot` (GNOME/KDE; may ask permission);
2. `grim` on Sway/Hyprland;
3. `gnome-screenshot` on GNOME;
4. `spectacle` on KDE.

On Ubuntu/GNOME, install a fallback if the portal denies the request:

```bash
sudo apt install gnome-screenshot
```

On KDE: `sudo apt install spectacle`. On wlroots: `sudo apt install grim`.

Wayland capture is the **full desktop**, not the monitor under the mouse.

## Shortcut

`spectra-hud --scan` talks to the running app over a local Unix socket. Bind it
to a custom shortcut:

- **GNOME:** Settings → Keyboard → Custom Shortcuts → `spectra-hud --scan`.
- **KDE:** System Settings → Shortcuts → Custom → `spectra-hud --scan`.

Other commands:

```bash
spectra-hud --ask     # ask about the current screen
spectra-hud --show    # command center
spectra-hud --pause   # private mode
spectra-hud --cancel  # cancel an in-flight scan
spectra-hud --quit
```

## What is different

- No anchored cards over other applications.
- No `pynput` global hotkeys; use the tray or a system shortcut.
- Window-title blocklist is not reliable on native Wayland; `private mode`
  still works.
- The overlay/command bar is replaced by normal windows.
- The tray uses AppIndicator/StatusNotifier and needs `python3-gi` and
  `gir1.2-ayatanaappindicator3-0.1`.
- The portal may show a permission dialog per capture; `ScreenCast` with a
  persistent token is the next step for a smoother flow.

## Smoke test

Run inside a Wayland session:

```bash
./scripts/wayland-check.sh
```

It checks the session, portal, backends and tray dependencies, then captures
the screen and saves `${XDG_RUNTIME_DIR}/spectra-wayland-test.png`.

## Status

Wayland mode is **beta**. The `v0.3.0-beta` packages include it; the
`v0.2.1` release remains the stable X11-only package.

Validated on 2026-10-26 in a nested **Sway 1.9** session with `grim` and
XWayland: capture, Results panel, card follow-up and `--scan` IPC. The portal
client was also validated against `xdg-desktop-portal-wlr` in a private
session; the GNOME and KDE portal **backends** still need a real session test.
