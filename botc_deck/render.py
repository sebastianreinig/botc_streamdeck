import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Canvas dimensions for Stream Deck MK.2
KEY_SIZE = (72, 72)

# Color Palette (BotC Dark Gothic)
COLOR_BG_DEFAULT = (20, 22, 30)
COLOR_BG_ACTIVE = (35, 40, 58)
COLOR_BORDER_DEFAULT = (45, 52, 70)
COLOR_TEXT_PRIMARY = (240, 240, 245)
COLOR_TEXT_MUTED = (160, 165, 180)

# Specialized Colors
COLOR_NIGHT = (108, 92, 231)       # Violet / Night
COLOR_DAY = (243, 156, 18)         # Warm Sun Gold
COLOR_BELL = (230, 126, 34)        # Brass Bell
COLOR_TIMER_ACTIVE = (9, 132, 227) # Bright Blue
COLOR_TIMER_WARN = (231, 76, 60)   # Vivid Red / Alert
COLOR_BT_OK = (0, 184, 148)        # Emerald Green
COLOR_BT_WAIT = (253, 203, 110)    # Amber
COLOR_BT_OFF = (100, 110, 125)     # Dim Grey
COLOR_CANCEL = (214, 48, 49)       # Red

class ButtonRenderer:
    def __init__(self, assets_dir=None):
        self.assets_dir = Path(assets_dir) if assets_dir else Path("assets/icons")
        self.icon_cache = {}
        self._load_fonts()

    def _load_fonts(self):
        # Try loading high quality TrueType fonts commonly found on Linux / macOS
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        chosen_font = None
        for path in font_candidates:
            if os.path.exists(path):
                chosen_font = path
                break

        try:
            if chosen_font:
                self.font_large = ImageFont.truetype(chosen_font, 18)
                self.font_medium = ImageFont.truetype(chosen_font, 12)
                self.font_small = ImageFont.truetype(chosen_font, 9)
                self.font_timer = ImageFont.truetype(chosen_font, 20)
            else:
                self.font_large = ImageFont.load_default()
                self.font_medium = ImageFont.load_default()
                self.font_small = ImageFont.load_default()
                self.font_timer = ImageFont.load_default()
        except Exception:
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_timer = ImageFont.load_default()

    def load_icon(self, icon_name, size=(36, 36)):
        """Load and cache icon image from assets directory."""
        if not icon_name:
            return None
        cache_key = (icon_name, size)
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]

        icon_path = self.assets_dir / f"{icon_name}.png"
        if icon_path.exists():
            try:
                img = Image.open(icon_path).convert("RGBA")
                img = img.resize(size, Image.Resampling.LANCZOS)
                self.icon_cache[cache_key] = img
                return img
            except Exception as e:
                print(f"[Renderer] Failed loading icon {icon_name}: {e}")
        return None

    def render_button(
        self,
        label=None,
        sublabel=None,
        icon_name=None,
        bg_color=COLOR_BG_DEFAULT,
        border_color=COLOR_BORDER_DEFAULT,
        border_width=2,
        is_active=False,
        highlight_color=None,
        custom_icon_img=None,
    ):
        """Render a single 72x72 Stream Deck button image."""
        img = Image.new("RGBA", KEY_SIZE, bg_color)
        draw = ImageDraw.Draw(img)

        # Background accent if active
        if is_active and highlight_color:
            border_color = highlight_color
            border_width = 3
            # Subtle gradient or inner fill tint
            inner_box = [(4, 4), (KEY_SIZE[0] - 5, KEY_SIZE[1] - 5)]
            draw.rounded_rectangle(inner_box, radius=8, fill=(highlight_color[0]//4, highlight_color[1]//4, highlight_color[2]//4))

        # Rounded border
        box = [(1, 1), (KEY_SIZE[0] - 2, KEY_SIZE[1] - 2)]
        draw.rounded_rectangle(box, radius=9, outline=border_color, width=border_width)

        # Place icon if available
        icon = custom_icon_img or self.load_icon(icon_name)
        if icon:
            # Position icon upper center
            icon_x = (KEY_SIZE[0] - icon.width) // 2
            icon_y = 6 if (label or sublabel) else (KEY_SIZE[1] - icon.height) // 2
            img.alpha_composite(icon, (icon_x, icon_y))

        # Place labels
        if label:
            font = self.font_medium
            # Text bounding box
            bbox = draw.textbbox((0, 0), label, font=font)
            text_w = bbox[2] - bbox[0]
            text_x = (KEY_SIZE[0] - text_w) // 2

            if icon:
                text_y = KEY_SIZE[1] - (22 if sublabel else 18)
            else:
                text_y = (KEY_SIZE[1] - (bbox[3] - bbox[1])) // 2 if not sublabel else 18

            color = highlight_color if is_active and highlight_color else COLOR_TEXT_PRIMARY
            draw.text((text_x, text_y), label, font=font, fill=color)

        if sublabel:
            bbox_sub = draw.textbbox((0, 0), sublabel, font=self.font_small)
            sub_w = bbox_sub[2] - bbox_sub[0]
            sub_x = (KEY_SIZE[0] - sub_w) // 2
            sub_y = KEY_SIZE[1] - 13
            draw.text((sub_x, sub_y), sublabel, font=self.font_small, fill=COLOR_TEXT_MUTED)

        return img.convert("RGB")

    def render_timer_button(self, label, remaining_str=None, is_active=False, is_warning=False, is_alert=False):
        """Render a dedicated countdown timer button with live ticking text."""
        bg = COLOR_BG_DEFAULT
        border = COLOR_BORDER_DEFAULT
        border_w = 2
        text_color = COLOR_TEXT_PRIMARY

        if is_active:
            if is_alert:
                bg = (80, 10, 10)
                border = COLOR_CANCEL
                text_color = (255, 100, 100)
                border_w = 4
            elif is_warning:
                bg = (60, 35, 10)
                border = COLOR_TIMER_WARN
                text_color = (255, 180, 100)
                border_w = 3
            else:
                bg = (10, 35, 65)
                border = COLOR_TIMER_ACTIVE
                text_color = (120, 200, 255)
                border_w = 3

        img = Image.new("RGBA", KEY_SIZE, bg)
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([(1, 1), (KEY_SIZE[0] - 2, KEY_SIZE[1] - 2)], radius=9, outline=border, width=border_w)

        if is_active and remaining_str:
            # Display big remaining time
            font = self.font_timer if len(remaining_str) <= 5 else self.font_large
            bbox = draw.textbbox((0, 0), remaining_str, font=font)
            tx = (KEY_SIZE[0] - (bbox[2] - bbox[0])) // 2
            ty = 16
            draw.text((tx, ty), remaining_str, font=font, fill=text_color)

            # Sublabel: e.g. "10 Min"
            sub_bbox = draw.textbbox((0, 0), label, font=self.font_small)
            sx = (KEY_SIZE[0] - (sub_bbox[2] - sub_bbox[0])) // 2
            draw.text((sx, KEY_SIZE[1] - 15), label, font=self.font_small, fill=COLOR_TEXT_MUTED)
        else:
            # Normal inactive view
            icon = self.load_icon("timer", size=(30, 30))
            if icon:
                img.alpha_composite(icon, ((KEY_SIZE[0] - 30) // 2, 8))
            bbox = draw.textbbox((0, 0), label, font=self.font_medium)
            tx = (KEY_SIZE[0] - (bbox[2] - bbox[0])) // 2
            draw.text((tx, KEY_SIZE[1] - 22), label, font=self.font_medium, fill=COLOR_TEXT_PRIMARY)

        return img.convert("RGB")
