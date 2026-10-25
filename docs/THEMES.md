# Themes

The command center ships with 10 palettes: 5 dark and 5 light. Pick one in the
theme grid or press `Ctrl+T` to cycle. The choice is saved in
`~/.config/spectra-hud/config.json` and applies to the command center, the HUD
cards, the scan indicator and the prompt.

## Dark

| Theme | Mood | Accent |
|---|---|---|
| **Spectra** | warm near-black, instrument panel | safety orange |
| **Phosphor** | CRT / terminal green | phosphor green |
| **Ice** | cold navy | ice blue |
| **Ember** | warm black / forge | amber |
| **Plasma** | deep plum | magenta |

## Light

| Theme | Mood | Accent |
|---|---|---|
| **Paper** | warm paper, ink | burnt orange |
| **Blueprint** | technical drawing | cobalt |
| **Terminal** | pale green | forest green |
| **Sand** | warm desert | terracotta |
| **Mono** | stark white | signal red |

## Notes

- Light themes keep dark text on light cards; the target bar uses the accent.
- The theme affects the app (Tk), not the public website, which stays on the
  Spectra identity.
- If you add a theme, put it in `theme.py` with every token and add a test.
