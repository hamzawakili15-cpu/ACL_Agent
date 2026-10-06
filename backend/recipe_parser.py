"""Conservative plain-text recipe parser for FastEat AI.

Reorganizes text the agent actually produced into sections.
It never invents content: anything that cannot be recognized stays available
in the returned ``raw_text``, which the frontend can always display.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

_HEADING_MAP: Dict[str, str] = {
    "ingredients": "ingredients",
    "ingredient list": "ingredients",
    "ingredients needed": "ingredients",
    "list of ingredients": "ingredients",
    "instructions": "instructions",
    "directions": "instructions",
    "steps": "instructions",
    "step by step": "instructions",
    "step-by-step instructions": "instructions",
    "cooking steps": "instructions",
    "recipe steps": "instructions",
    "method": "instructions",
    "preparation": "instructions",
    "preparation steps": "instructions",
    "how to make": "instructions",
    "how to cook": "instructions",
    "tips": "tips",
    "cooking tips": "tips",
    "tips and tricks": "tips",
    "tips & tricks": "tips",
    "tools": "tools",
    "tools needed": "tools",
    "kitchen tools": "tools",
    "equipment": "tools",
    "variations": "variations",
    "recipe variations": "variations",
    "similar recipes": "similar_recipes",
    "sources": "sources",
    "source": "sources",
    "references": "sources",
    "notes": "notes",
    "nutrition": "nutrition",
}

_META_MAP: Dict[str, str] = {
    "prep time": "prep_time",
    "preparation time": "prep_time",
    "cook time": "cook_time",
    "cooking time": "cook_time",
    "servings": "servings",
    "serves": "servings",
    "yield": "servings",
    "difficulty": "difficulty",
}

_UNITS = {
    "cup", "cups", "tbsp", "tbs", "tablespoon", "tablespoons",
    "tsp", "teaspoon", "teaspoons", "g", "gram", "grams", "kg",
    "kilogram", "kilograms", "ml", "l", "liter", "liters", "litre",
    "litres", "oz", "ounce", "ounces", "lb", "lbs", "pound", "pounds",
    "slice", "slices", "clove", "cloves", "piece", "pieces", "bunch",
    "bunches", "can", "cans", "packet", "packets", "box", "boxes",
    "jar", "jars", "stick", "sticks", "pinch", "pinches", "dash",
    "handful", "sprig", "sprigs", "leaves", "wedge", "wedges",
    "bottle", "bottles", "bowl", "bowls", "glass", "glasses",
}

_LIST_PREFIX = re.compile(r"^\s*(?:[-*•–—]|\(?\d{1,2}[.)])\s+(.*)$")
_MD_HEADING = re.compile(r"^\s*#{1,6}\s+(.*?)\s*#*\s*$")
_BOLD_LINE = re.compile(r"^\s*\*\*(.+?)\*\*\s*:?\s*$")
_COLON_LINE = re.compile(r"^\s*([A-Za-z][A-Za-z &/''-]{0,60}):\s*$")
_META_LINE = re.compile(
    r"^\s*\**\s*(prep\s*time|preparation\s*time|cook\s*time|cooking\s*time|"
    r"servings?|serves|yield|difficulty)\s*:\s*\**\s*(.+?)\s*\**\s*$",
    re.IGNORECASE,
)
_RECIPE_NAME = re.compile(
    r"^\s*\**\s*(?:recipe\s*name|name\s*of\s*(?:the\s*)?recipe|recipe)\s*:\s*\**\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)
_QUANTITY = re.compile(
    r"^(?P<amount>\d+\s+\d+\s*/\s*\d+|\d+\s*/\s*\d+"
    r"|\d+(?:[.,]\d+)?(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?"
    r"|[½¼¾⅓⅔⅛⅜⅝⅞](?:\s*\d+)?)"
    r"\s+(?P<rest>\S.*)$"
)
_URL = re.compile(r"https?://[^\s\]\)}>\"]+")
_COMPACT_QTY = re.compile(
    r"^(?P<amount>\d+(?:[.,]\d+)?)\s*(?P<unit>g|kg|ml|l|oz|lb|lbs)\b\s*(?P<name>\S.*)$",
    re.IGNORECASE,
)


def _strip_md(text: str) -> str:
    text = re.sub(r"[*_`]{1,3}", "", text)
    return text.strip(" \t:-")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", _strip_md(text)).strip().lower()


def _lookup(label: str) -> Optional[str]:
    key = _normalize(label)
    if not key:
        return None
    if key in _HEADING_MAP:
        return _HEADING_MAP[key]
    for candidate in sorted(_HEADING_MAP, key=len, reverse=True):
        if key.startswith(candidate) and len(key) - len(candidate) <= 15:
            return _HEADING_MAP[candidate]
    return None


def _as_heading(line: str) -> Optional[str]:
    """Return a section key if the line is a recognizable section heading."""
    stripped = line.strip()
    if not stripped or len(stripped) > 90 or _LIST_PREFIX.match(stripped):
        return None
    label: Optional[str] = None
    if md := _MD_HEADING.match(stripped):
        label = md.group(1)
    elif bold := _BOLD_LINE.match(stripped):
        label = bold.group(1)
    elif colon := _COLON_LINE.match(stripped):
        label = colon.group(1)
    elif stripped.endswith(":") and len(stripped) <= 40:
        label = stripped
    elif (
        not stripped.endswith((".", "!", "?", ",", ";"))
        and len(stripped) <= 30
        and stripped.lower() in _HEADING_MAP
    ):
        label = stripped
    if label is None:
        return None
    return _lookup(label)


def _split_paragraphs(lines: List[str]) -> List[List[str]]:
    paragraphs: List[List[str]] = []
    current: List[str] = []
    for line in lines:
        if line.strip():
            current.append(line)
        elif current:
            paragraphs.append(current)
            current = []
    if current:
        paragraphs.append(current)
    return paragraphs


def _list_items(lines: List[str]) -> List[str]:
    """Turn a section's lines into items, dropping decorative numbering."""
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return []
    marked = [m for line in non_empty if (m := _LIST_PREFIX.match(line))]
    if marked and len(marked) >= len(non_empty) * 0.5:
        return [_strip_md(m.group(1)) for m in marked if _strip_md(m.group(1))]
    return [
        _strip_md(" ".join(paragraph)) for paragraph in _split_paragraphs(non_empty)
    ]


def _parse_ingredient(line: str) -> Tuple[str, str, str]:
    text = _strip_md(line)
    if not text:
        return "", "", ""
    match = _QUANTITY.match(text)
    if not match:
        if compact := _COMPACT_QTY.match(text):
            return _strip_md(compact.group("name")), compact.group("amount"), compact.group("unit")
        return text, "", ""
    amount = match.group("amount")
    rest = match.group("rest")
    first, _, remainder = rest.partition(" ")
    if first.lower().rstrip("s") in {u.rstrip("s") for u in _UNITS} and remainder:
        return _strip_md(remainder), amount, first
    return _strip_md(rest), amount, ""


def _clean_title(line: str) -> str:
    return _strip_md(line)


def parse_recipe(raw_text: str) -> Dict[str, object]:
    """Parse the agent's plain text into a structured recipe dictionary."""
    text = (raw_text or "").replace("\r\n", "\n").replace("\r", "\n")

    recipe: Dict[str, object] = {
        "title": "",
        "description": "",
        "ingredients": [],
        "instructions": [],
        "prep_time": "",
        "cook_time": "",
        "servings": "",
        "difficulty": "",
        "tips": [],
        "source_urls": [],
        "sections": [],
        "raw_text": raw_text or "",
    }
    if not text.strip():
        return recipe

    preamble: List[str] = []
    buckets: Dict[str, List[str]] = {}
    current: Optional[str] = None

    for line in text.split("\n"):
        if meta := _META_LINE.match(line):
            key = _META_MAP[_normalize(meta.group(1))]
            if not recipe[key]:
                recipe[key] = _strip_md(meta.group(2))
            continue
        heading = _as_heading(line)
        if heading:
            current = heading
            buckets.setdefault(heading, [])
            continue
        if current is None:
            preamble.append(line)
        else:
            buckets[current].append(line)

    title_match = _RECIPE_NAME.search(text)
    title_line = ""
    if title_match:
        recipe["title"] = _strip_md(title_match.group(1))
    else:
        for line in preamble:
            if line.strip():
                title_line = line.strip()
                break
        if title_line and not title_line.endswith("."):
            recipe["title"] = _clean_title(title_line)

    description: List[str] = []
    for paragraph in _split_paragraphs(preamble):
        para_text = _strip_md(" ".join(paragraph))
        if title_line and paragraph[0].strip() == title_line:
            para_text = _strip_md(" ".join(paragraph[1:]))
        if para_text and not _as_heading(paragraph[0]) and len(para_text) >= 25:
            description.append(para_text)
            break
    if not description and title_line.endswith("."):
        para_text = _strip_md(title_line)
        if len(para_text) >= 25:
            description.append(para_text)
    recipe["description"] = description[0] if description else ""

    if lines := buckets.get("ingredients"):
        ingredients = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.endswith(":") and not _QUANTITY.match(_strip_md(stripped)):
                continue
            name, amount, unit = _parse_ingredient(stripped)
            if name:
                ingredients.append({"name": name, "amount": amount, "unit": unit})
        recipe["ingredients"] = ingredients

    if lines := buckets.get("instructions"):
        recipe["instructions"] = _list_items(lines)

    if lines := buckets.get("tips"):
        recipe["tips"] = _list_items(lines)

    servings = str(recipe.get("servings") or "").strip()
    if servings.isdigit():
        recipe["servings"] = int(servings)
    else:
        recipe["servings"] = servings

    seen: List[str] = []
    for url in _URL.findall(text):
        clean = url.rstrip(".,;:)]}>\"'")
        if clean not in seen:
            seen.append(clean)
    recipe["source_urls"] = seen

    sections = []
    for key, lines in buckets.items():
        if key in ("ingredients", "instructions", "tips"):
            continue
        body = "\n".join(line for line in lines if line.strip()).strip()
        if not body:
            continue
        sections.append({
            "heading": key.replace("_", " ").capitalize(),
            "body": body,
        })
    recipe["sections"] = sections

    return recipe
