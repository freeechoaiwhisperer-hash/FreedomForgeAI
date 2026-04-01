# ============================================================
#  FreedomForge AI — assets/themes.py
#  Theme definitions — every color in one place
# ============================================================

THEMES = {

    "Midnight": {
        "display":      "🌑  Midnight",
        "base":         "dark",
        "bg_deep":      "#080808",
        "bg_panel":     "#0f0f0f",
        "bg_card":      "#141414",
        "bg_input":     "#111111",
        "bg_sidebar":   "#0c0c0c",
        "bg_topbar":    "#080808",
        "bg_hover":     "#1a1a1a",
        "accent":       "#1a5a9a",
        "accent_hover": "#0d3d70",
        "accent2":      "#c8a2ff",
        "text_primary": "#dddddd",
        "text_secondary":"#666666",
        "text_dim":     "#333333",
        "text_you":     "#aaddff",
        "text_ai":      "#dddddd",
        "text_sys":     "#444444",
        "text_error":   "#ff6666",
        "gold":         "#FFD700",
        "green":        "#00cc66",
        "red":          "#ff4444",
        "yellow":       "#ffaa00",
        "purple":       "#c8a2ff",
        "border":       "#1e1e1e",
        "divider":      "#1a1a1a",
    },

    "Forge": {
        "display":      "🔥  Forge",
        "base":         "dark",
        "bg_deep":      "#0a0604",
        "bg_panel":     "#100b06",
        "bg_card":      "#160e07",
        "bg_input":     "#120c07",
        "bg_sidebar":   "#0d0804",
        "bg_topbar":    "#0a0604",
        "bg_hover":     "#1e1208",
        "accent":       "#b84a00",
        "accent_hover": "#8a3500",
        "accent2":      "#ffaa44",
        "text_primary": "#e8d5c0",
        "text_secondary":"#6a5040",
        "text_dim":     "#2e1e10",
        "text_you":     "#ffcc88",
        "text_ai":      "#e8d5c0",
        "text_sys":     "#4a3020",
        "text_error":   "#ff6644",
        "gold":         "#ffaa00",
        "green":        "#88cc44",
        "red":          "#ff4422",
        "yellow":       "#ffcc44",
        "purple":       "#cc88ff",
        "border":       "#201208",
        "divider":      "#1e1008",
    },

    "Aurora": {
        "display":      "🌌  Aurora",
        "base":         "dark",
        "bg_deep":      "#040810",
        "bg_panel":     "#070d18",
        "bg_card":      "#0a1220",
        "bg_input":     "#080e18",
        "bg_sidebar":   "#060a14",
        "bg_topbar":    "#040810",
        "bg_hover":     "#0e1828",
        "accent":       "#0066aa",
        "accent_hover": "#004488",
        "accent2":      "#44ffcc",
        "text_primary": "#c8e8ff",
        "text_secondary":"#446688",
        "text_dim":     "#1a2a3a",
        "text_you":     "#88ddff",
        "text_ai":      "#c8e8ff",
        "text_sys":     "#2a4a6a",
        "text_error":   "#ff6688",
        "gold":         "#44ffcc",
        "green":        "#44ffaa",
        "red":          "#ff4466",
        "yellow":       "#ffdd44",
        "purple":       "#aa88ff",
        "border":       "#0e1e30",
        "divider":      "#0c1a28",
    },

    "Ghost": {
        "display":      "👻  Ghost",
        "base":         "light",
        "bg_deep":      "#f8f8f8",
        "bg_panel":     "#f0f0f0",
        "bg_card":      "#e8e8e8",
        "bg_input":     "#eeeeee",
        "bg_sidebar":   "#e4e4e4",
        "bg_topbar":    "#f8f8f8",
        "bg_hover":     "#dcdcdc",
        "accent":       "#1a5a9a",
        "accent_hover": "#0d3d70",
        "accent2":      "#7744cc",
        "text_primary": "#111111",
        "text_secondary":"#888888",
        "text_dim":     "#bbbbbb",
        "text_you":     "#0044aa",
        "text_ai":      "#111111",
        "text_sys":     "#999999",
        "text_error":   "#cc2200",
        "gold":         "#cc8800",
        "green":        "#007744",
        "red":          "#cc2200",
        "yellow":       "#aa7700",
        "purple":       "#7744cc",
        "border":       "#d0d0d0",
        "divider":      "#dddddd",
    },

    "Matrix": {
        "display":      "💚  Matrix",
        "base":         "dark",
        "bg_deep":      "#000400",
        "bg_panel":     "#000800",
        "bg_card":      "#000d00",
        "bg_input":     "#000600",
        "bg_sidebar":   "#000600",
        "bg_topbar":    "#000400",
        "bg_hover":     "#001200",
        "accent":       "#008800",
        "accent_hover": "#005500",
        "accent2":      "#00ff44",
        "text_primary": "#00cc00",
        "text_secondary":"#006600",
        "text_dim":     "#002200",
        "text_you":     "#00ff88",
        "text_ai":      "#00cc00",
        "text_sys":     "#004400",
        "text_error":   "#ff4400",
        "gold":         "#00ff44",
        "green":        "#00ff00",
        "red":          "#ff2200",
        "yellow":       "#aaff00",
        "purple":       "#00ffcc",
        "border":       "#001800",
        "divider":      "#001400",
    },

}

DEFAULT_THEME = "Midnight"


def get(name: str) -> dict:
    return THEMES.get(name, THEMES[DEFAULT_THEME])


def names() -> list[str]:
    return list(THEMES.keys())


def display_names() -> list[str]:
    return [THEMES[k]["display"] for k in THEMES]


def name_from_display(display: str) -> str:
    for k, v in THEMES.items():
        if v["display"] == display:
            return k
    return DEFAULT_THEME
