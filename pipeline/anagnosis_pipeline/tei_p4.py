"""Loader for Perseus TEI P4 files (Middle Liddell, Jebb commentaries).

These files declare external DTDs and use named entities we cannot resolve offline, so
the DOCTYPE is stripped and entities are substituted textually before parsing.
"""
from __future__ import annotations

import html.entities
import re
from pathlib import Path

from lxml import etree

_EXTRA = {
    "verbar": "|", "equals": "=", "ast": "*", "colon": ":", "quest": "?", "breve": "˘",
    "macr": "¯", "dagger": "†", "sect": "§", "lsquo": "‘", "rsquo": "’", "ldquo": "“",
    "rdquo": "”", "mdash": "—", "ndash": "–", "hellip": "…", "amp": "&amp;", "lt": "&lt;",
    "gt": "&gt;", "quot": "&quot;", "apos": "&apos;",
    # Perseus boilerplate entities (header only)
    "responsibility": "", "fund.AnnCPB": "", "fund.NEH": "", "Perseus.publish": "",
}


def _entity(m: re.Match) -> str:
    name = m.group(1)
    if name.startswith("#"):
        return m.group(0)
    if name in _EXTRA:
        return _EXTRA[name]
    ch = html.entities.html5.get(name + ";")
    if ch is not None:
        return html.escape(ch, quote=False)
    raise ValueError(f"unknown entity &{name};")


def load(path: Path) -> etree._Element:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<\?xml[^>]*\?>", "", text, count=1)
    text = re.sub(r"<!DOCTYPE.*?\]>", "", text, count=1, flags=re.S)
    text = re.sub(r"&([A-Za-z#][\w.]*);", _entity, text)
    parser = etree.XMLParser(huge_tree=True, remove_blank_text=False)
    return etree.fromstring(text.encode("utf-8"), parser)
