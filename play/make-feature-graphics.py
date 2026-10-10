"""Draw the 1024x500 Google Play feature graphics: the reader's banner and one per text app.

White Noto Serif Medium on the app's colour, as in the reader's Ἀνάγνωσις banner. A text's
banner has its Greek title, "by <author>" (the New Testament: "New Testament") and a smaller
"for Anagnosis" line. Run from the repository root: python3 play/make-feature-graphics.py
Needs Pillow and Noto Serif (on Arch: noto-fonts).
"""
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/noto/NotoSerif-Medium.ttf"
W, H = 1024, 500
PLAY = Path(__file__).resolve().parent
APP = PLAY.parent / "app"

# slug: (Greek title, second line, app module whose launcher colour is used)
TEXTS = {
    "antigone": ("Ἀντιγόνη", "by Sophocles", "antigoneApp"),
    "ajax": ("Αἴας", "by Sophocles", "ajaxApp"),
    "electra": ("Ἠλέκτρα", "by Sophocles", "electraApp"),
    "odyssey": ("Ὀδύσσεια", "by Homer", "odysseyApp"),
    "symposium": ("Συμπόσιον", "by Plato", "symposiumApp"),
    "newtestament": ("Ἡ Καινὴ Διαθήκη", "New Testament", "newTestamentApp"),
}
READER_COLOUR = "#592c13"


def font_fitting(text: str, size: int, width: int) -> ImageFont.FreeTypeFont:
    """The font at `size`, or smaller if the text would be wider than `width`."""
    while True:
        f = ImageFont.truetype(FONT, size)
        bb = f.getbbox(text)
        if bb[2] - bb[0] <= width or size <= 10:
            return f
        size -= 1


def draw_lines(colour: str, lines: list[tuple[str, ImageFont.FreeTypeFont, int, int]]) -> Image.Image:
    """Lines (text, font, alpha, gap above) centred horizontally, the block centred vertically.
    Heights are those of the font's capitals and descenders, so that lines line up whatever their letters."""
    im = Image.new("RGB", (W, H), colour)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    boxes = []
    for text, f, alpha, gap in lines:
        top, bottom = f.getbbox("ΗΓgj")[1], f.getbbox("ΗΓgj")[3]
        boxes.append((top, bottom, gap))
    total = sum(b - t + g for t, b, g in boxes)
    y = (H - total) / 2
    for (text, f, alpha, _), (top, bottom, gap) in zip(lines, boxes):
        y += gap
        bb = d.textbbox((0, 0), text, font=f)
        d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], y - top), text, font=f, fill=(255, 255, 255, alpha))
        y += bottom - top
    im.paste(layer, (0, 0), layer)
    return im


def launcher_colour(module: str) -> str:
    xml = (APP / module / "src/main/res/values/colors.xml").read_text()
    return "#" + re.search(r"#([0-9a-fA-F]{6})", xml).group(1)


def main() -> None:
    # the reader: the title as in the original banner, the subtitle fitted to its width
    title = ImageFont.truetype(FONT, 164)
    tw = title.getbbox("Ἀνάγνωσις")[2] - title.getbbox("Ἀνάγνωσις")[0]
    draw_lines(READER_COLOUR, [
        ("Ἀνάγνωσις", title, 255, 0),
        ("An Ancient Greek Reading App", font_fitting("An Ancient Greek Reading App", 77, tw), 255, 40),
    ]).save(PLAY / "feature-graphic.png")
    for slug, (greek, second, module) in TEXTS.items():
        draw_lines(launcher_colour(module), [
            (greek, font_fitting(greek, 150, 880), 255, 0),
            (second, ImageFont.truetype(FONT, 60), 255, 28),
            ("for Anagnosis · Ancient Greek Reading App", ImageFont.truetype(FONT, 32), 210, 44),
        ]).save(PLAY / f"{slug}-feature-graphic.png")
        print(slug)


if __name__ == "__main__":
    main()
