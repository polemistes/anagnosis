#!/usr/bin/env python3
"""Fix the rho-with-breathing glyphs in Cardo Regular 1.0451.

In the Regular weight, ῤ (U+1FE4), ῥ (U+1FE5) and Ῥ (U+1FEC) are composites of the letter and
a zero-width combining breathing placed at (almost) no offset. A zero-width mark is drawn to the
left of its origin, so the breathing lands before the letter, over the end of the word before.
The Bold weight builds the same three glyphs correctly: this script moves the Regular's marks
so that they sit where the Bold's sit, relative to the letter, and recomputes the bounds.

Cardo is under the SIL Open Font License 1.1 with no Reserved Font Name, so the modified file
keeps its name; the licence file notes the change. Idempotent.

Usage: fix-cardo-rho.py <cardo_regular.ttf> <cardo_bold.ttf>
"""
import sys
from fontTools.ttLib import TTFont

GLYPHS = {0x1FE4: "uni0313", 0x1FE5: "uni0314", 0x1FEC: "uni0314"}


def absolute_centre(font, glyph_name, mark):
    """Horizontal centre of the mark component's outline, and of the letter's, within the glyph."""
    glyf = font["glyf"]
    composite = glyf[glyph_name]
    letter = mark_centre = None
    for component in composite.components:
        part = glyf[component.glyphName]
        centre = component.x + (part.xMin + part.xMax) / 2
        if component.glyphName == mark:
            mark_centre, mark_y = centre, component.y
        else:
            letter = centre
    return letter, mark_centre, mark_y


def main(regular_path, bold_path):
    regular, bold = TTFont(regular_path), TTFont(bold_path)
    glyf, hmtx = regular["glyf"], regular["hmtx"]
    cmap, bold_cmap = regular.getBestCmap(), bold.getBestCmap()
    changed = 0
    for codepoint, mark in GLYPHS.items():
        name, bold_name = cmap[codepoint], bold_cmap[codepoint]
        letter, mark_centre, _ = absolute_centre(regular, name, mark)
        bold_letter, bold_mark, bold_y = absolute_centre(bold, bold_name, mark)
        shift = (bold_mark - bold_letter) - (mark_centre - letter)
        composite = glyf[name]
        for component in composite.components:
            if component.glyphName == mark:
                old = (component.x, component.y)
                component.x = round(component.x + shift)
                component.y = bold_y
                if (component.x, component.y) != old:
                    changed += 1
                print(f"{chr(codepoint)} {name}: {mark} at {old} -> ({component.x}, {component.y})")
        composite.recalcBounds(glyf)
        advance, _ = hmtx[name]
        hmtx[name] = (advance, composite.xMin)
        print(f"   bounds now x {composite.xMin}..{composite.xMax}, advance {advance}")
    if changed:
        regular.save(regular_path)
        print(f"saved {regular_path}")
    else:
        print("nothing to change")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
