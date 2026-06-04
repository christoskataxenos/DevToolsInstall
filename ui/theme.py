import customtkinter as ctk

# Premium Palette (Dark / Light tuples)
COLORS = {
    "bg": ("#F3F4F6", "#0F172A"),            # Light gray / Dark slate
    "sidebar": ("#E5E7EB", "#1E293B"),       # Gray / Slate-800
    "card": ("#FFFFFF", "#1E293B"),          # White / Slate-800
    "card_border": ("#D1D5DB", "#334155"),   # Light border / Slate-700
    "text": ("#1E293B", "#F8FAFC"),          # Dark slate / Off-white
    "text_dim": ("#64748B", "#94A3B8"),      # Muted slate
    "accent": ("#3B82F6", "#60A5FA"),        # Blue-500 / Blue-400
    "accent_hover": ("#2563EB", "#3B82F6"),  # Hover blue
    "success": ("#10B981", "#34D399"),       # Emerald-500 / Emerald-400
    "warning": ("#F59E0B", "#FBBF24"),       # Amber-500 / Amber-400
    "error": ("#EF4444", "#F87171"),         # Red-500 / Red-400
    "terminal_bg": ("#0F172A", "#090D16"),   # Pure dark for terminal view
    "terminal_fg": ("#10B981", "#34D399")    # Matrix green
}

FONTS = {
    "header": ("Segoe UI", 16, "bold"),
    "subheader": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 12),
    "bold": ("Segoe UI", 12, "bold"),
    "small": ("Segoe UI", 10),
    "mono": ("Consolas", 10)
}

def init_theme() -> None:
    """Initializes CustomTkinter's default dark styling setup."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
