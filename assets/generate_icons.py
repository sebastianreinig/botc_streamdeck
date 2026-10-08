#!/usr/bin/env python3
"""
Procedural icon generator for BotC Stream Deck.
Generates clean, high-contrast 72x72 PNG icons with alpha channel.
"""
from pathlib import Path
from PIL import Image, ImageDraw

def create_icons(output_dir="assets/icons"):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    size = (72, 72)

    def new_canvas():
        return Image.new("RGBA", size, (0, 0, 0, 0))

    # 1. Moon (Night)
    img = new_canvas()
    d = ImageDraw.Draw(img)
    # Outer circle
    d.ellipse([(14, 12), (58, 56)], fill=(160, 150, 245))
    # Cutout circle to make crescent
    d.ellipse([(24, 8), (66, 50)], fill=(0, 0, 0, 0))
    img.save(out / "moon.png")

    # 2. Sun (Day)
    img = new_canvas()
    d = ImageDraw.Draw(img)
    # Center
    d.ellipse([(22, 22), (50, 50)], fill=(255, 175, 40))
    # Rays
    ray_coords = [
        [(34, 8), (38, 18)], [(34, 54), (38, 64)],
        [(8, 34), (18, 38)], [(54, 34), (64, 38)],
        [(16, 16), (24, 24)], [(48, 48), (56, 56)],
        [(48, 16), (56, 24)], [(16, 48), (24, 56)]
    ]
    for r in ray_coords:
        d.line([(r[0][0], r[0][1]), (r[1][0], r[1][1])], fill=(255, 175, 40), width=4)
    img.save(out / "sun.png")

    # 3. Play / Pause
    img = new_canvas()
    d = ImageDraw.Draw(img)
    # Triangle play
    d.polygon([(16, 18), (16, 54), (38, 36)], fill=(230, 235, 245))
    # Two bars pause
    d.rectangle([(44, 20), (49, 52)], fill=(230, 235, 245))
    d.rectangle([(54, 20), (59, 52)], fill=(230, 235, 245))
    img.save(out / "play_pause.png")

    # 4. Vol Down
    img = new_canvas()
    d = ImageDraw.Draw(img)
    # Speaker cone
    d.polygon([(12, 28), (24, 28), (38, 16), (38, 56), (24, 44), (12, 44)], fill=(200, 210, 230))
    # Minus sign
    d.rectangle([(48, 34), (62, 38)], fill=(200, 210, 230))
    img.save(out / "vol_down.png")

    # 5. Vol Up
    img = new_canvas()
    d = ImageDraw.Draw(img)
    # Speaker cone
    d.polygon([(12, 28), (24, 28), (38, 16), (38, 56), (24, 44), (12, 44)], fill=(200, 210, 230))
    # Plus sign
    d.rectangle([(46, 34), (62, 38)], fill=(200, 210, 230))
    d.rectangle([(52, 28), (56, 44)], fill=(200, 210, 230))
    img.save(out / "vol_up.png")

    # 6. Timer (Stopwatch)
    img = new_canvas()
    d = ImageDraw.Draw(img)
    # Watch body
    d.ellipse([(14, 18), (58, 62)], outline=(100, 180, 255), width=4)
    # Top pin
    d.rectangle([(32, 10), (40, 16)], fill=(100, 180, 255))
    # Hands
    d.line([(36, 40), (36, 26)], fill=(100, 180, 255), width=3)
    d.line([(36, 40), (46, 40)], fill=(100, 180, 255), width=3)
    img.save(out / "timer.png")

    # 7. Cancel / Stop (X)
    img = new_canvas()
    d = ImageDraw.Draw(img)
    d.line([(18, 18), (54, 54)], fill=(235, 70, 70), width=6)
    d.line([(18, 54), (54, 18)], fill=(235, 70, 70), width=6)
    img.save(out / "cancel.png")

    # 8. Bell
    img = new_canvas()
    d = ImageDraw.Draw(img)
    # Dome
    d.pieslice([(18, 16), (54, 52)], 180, 360, fill=(245, 180, 45))
    d.rounded_rectangle([(14, 42), (58, 48)], radius=3, fill=(245, 180, 45))
    # Clapper
    d.ellipse([(31, 48), (41, 58)], fill=(205, 140, 25))
    # Top handle
    d.ellipse([(31, 10), (41, 20)], outline=(245, 180, 45), width=3)
    img.save(out / "bell.png")

    # 9. Bluetooth
    img = new_canvas()
    d = ImageDraw.Draw(img)
    # Classic BT rune
    points = [(36, 12), (36, 60), (48, 48), (24, 24), (48, 24), (36, 12)]
    d.line(points, fill=(60, 160, 255), width=4, joint="curve")
    d.line([(24, 48), (36, 36)], fill=(60, 160, 255), width=4)
    img.save(out / "bluetooth.png")

    # 10. Status / Info
    img = new_canvas()
    d = ImageDraw.Draw(img)
    d.ellipse([(14, 14), (58, 58)], outline=(120, 220, 180), width=4)
    d.ellipse([(33, 22), (39, 28)], fill=(120, 220, 180))
    d.rectangle([(33, 33), (39, 50)], fill=(120, 220, 180))
    img.save(out / "status.png")

    # 11. Brightness
    img = new_canvas()
    d = ImageDraw.Draw(img)
    d.ellipse([(20, 20), (52, 52)], fill=(220, 220, 160))
    d.pieslice([(20, 20), (52, 52)], 90, 270, fill=(80, 80, 60))
    img.save(out / "brightness.png")

    # 12. Power
    img = new_canvas()
    d = ImageDraw.Draw(img)
    d.arc([(16, 16), (56, 56)], start=300, end=240, fill=(240, 80, 80), width=5)
    d.line([(36, 12), (36, 34)], fill=(240, 80, 80), width=5)
    img.save(out / "power.png")

    # 13. Back
    img = new_canvas()
    d = ImageDraw.Draw(img)
    d.polygon([(16, 36), (36, 18), (36, 28), (56, 28), (56, 44), (36, 44), (36, 54)], fill=(200, 205, 220))
    img.save(out / "back.png")

    # 14. Search
    img = new_canvas()
    d = ImageDraw.Draw(img)
    d.ellipse([(16, 16), (46, 46)], outline=(100, 200, 255), width=4)
    d.line([(40, 40), (58, 58)], fill=(100, 200, 255), width=5)
    img.save(out / "search.png")

    # 15. Speaker
    img = new_canvas()
    d = ImageDraw.Draw(img)
    d.polygon([(16, 26), (28, 26), (44, 14), (44, 58), (28, 46), (16, 46)], fill=(120, 200, 240))
    d.arc([(40, 24), (54, 48)], start=-60, end=60, fill=(120, 200, 240), width=3)
    d.arc([(38, 16), (62, 56)], start=-60, end=60, fill=(120, 200, 240), width=3)
    img.save(out / "speaker.png")

    # 16. Refresh
    img = new_canvas()
    d = ImageDraw.Draw(img)
    d.arc([(18, 18), (54, 54)], start=30, end=300, fill=(100, 220, 160), width=4)
    d.polygon([(52, 20), (60, 32), (46, 32)], fill=(100, 220, 160))
    img.save(out / "reconnect.png")

    # 17. WiFi
    img = new_canvas()
    d = ImageDraw.Draw(img)
    # Radiating arcs
    d.arc([(12, 14), (60, 62)], start=225, end=315, fill=(80, 200, 255), width=4)
    d.arc([(20, 22), (52, 54)], start=225, end=315, fill=(80, 200, 255), width=4)
    d.arc([(28, 30), (44, 46)], start=225, end=315, fill=(80, 200, 255), width=4)
    d.ellipse([(33, 49), (39, 55)], fill=(80, 200, 255))
    img.save(out / "wifi.png")

    print(f"Generated {len(list(out.glob('*.png')))} icons in {out}")

if __name__ == "__main__":
    create_icons()
