import platform


def is_macos():
    return platform.system() == "Darwin"


# macOS system color names -- these automatically adapt to light/dark mode
# Tk resolves them at render time, so widgets update when the OS appearance changes.
MACOS_PALETTE = {
    "entry_bg": "systemTextBackgroundColor",
    "entry_fg": "systemTextColor",
    "listbox_bg": "systemTextBackgroundColor",
    "listbox_fg": "systemTextColor",
    "text_bg": "systemTextBackgroundColor",
    "text_fg": "systemTextColor",
    "highlight_border": "systemSeparatorColor",
    "accent": "systemControlAccentColor",
    "light_text": "systemSecondaryLabelColor",
    "warning_fg": "#FF6B6B",
    "info_fg": "systemLinkColor",
    "drop_highlight_bg": "systemFindHighlightColor",
    "check_select": "systemTextBackgroundColor",
    "select_bg": "systemSelectedTextBackgroundColor",
    "select_fg": "systemSelectedTextColor",
    "insert_bg": "systemTextColor",
}

# Fallback for non-macOS (Linux/Windows) -- hardcoded light colors
FALLBACK_PALETTE = {
    "entry_bg": "#ffffff",
    "entry_fg": "#1d1d1f",
    "listbox_bg": "#ffffff",
    "listbox_fg": "#1d1d1f",
    "text_bg": "#ffffff",
    "text_fg": "#1d1d1f",
    "highlight_border": "#d2d2d7",
    "accent": "#007AFF",
    "light_text": "#86868b",
    "warning_fg": "#FF6B6B",
    "info_fg": "#4A90E2",
    "drop_highlight_bg": "#E8F0FE",
    "check_select": "#ffffff",
    "select_bg": "#007AFF",
    "select_fg": "#ffffff",
    "insert_bg": "#1d1d1f",
}


def get_palette(override=None):
    """Return the appropriate color palette.

    On macOS, uses system color names that automatically follow
    the OS light/dark mode setting -- no restart needed.

    Args:
        override: Ignored on macOS (system colors always adapt).
                  On other platforms, returns the fallback palette.
    """
    if is_macos():
        return MACOS_PALETTE
    return FALLBACK_PALETTE
