"""HTML and CSS color literals, and the text to write when one of them changes."""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEX = re.compile(r"(?<![A-Za-z0-9_])#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})(?![0-9A-Fa-f])")
_FUNC = re.compile(r"(?<![A-Za-z0-9_-])(rgba?|hsla?)\(\s*([^)]{1,80})\)", re.IGNORECASE)
_NAME = re.compile(r"(?<![A-Za-z0-9_-])([A-Za-z]{3,20})(?![A-Za-z0-9_-])")

_NAMED = {
    "aliceblue": (240, 248, 255),
    "antiquewhite": (250, 235, 215),
    "aqua": (0, 255, 255),
    "aquamarine": (127, 255, 212),
    "azure": (240, 255, 255),
    "beige": (245, 245, 220),
    "bisque": (255, 228, 196),
    "black": (0, 0, 0),
    "blanchedalmond": (255, 235, 205),
    "blue": (0, 0, 255),
    "blueviolet": (138, 43, 226),
    "brown": (165, 42, 42),
    "burlywood": (222, 184, 135),
    "cadetblue": (95, 158, 160),
    "chartreuse": (127, 255, 0),
    "chocolate": (210, 105, 30),
    "coral": (255, 127, 80),
    "cornflowerblue": (100, 149, 237),
    "cornsilk": (255, 248, 220),
    "crimson": (220, 20, 60),
    "cyan": (0, 255, 255),
    "darkblue": (0, 0, 139),
    "darkcyan": (0, 139, 139),
    "darkgoldenrod": (184, 134, 11),
    "darkgray": (169, 169, 169),
    "darkgreen": (0, 100, 0),
    "darkgrey": (169, 169, 169),
    "darkkhaki": (189, 183, 107),
    "darkmagenta": (139, 0, 139),
    "darkolivegreen": (85, 107, 47),
    "darkorange": (255, 140, 0),
    "darkorchid": (153, 50, 204),
    "darkred": (139, 0, 0),
    "darksalmon": (233, 150, 122),
    "darkseagreen": (143, 188, 143),
    "darkslateblue": (72, 61, 139),
    "darkslategray": (47, 79, 79),
    "darkslategrey": (47, 79, 79),
    "darkturquoise": (0, 206, 209),
    "darkviolet": (148, 0, 211),
    "deeppink": (255, 20, 147),
    "deepskyblue": (0, 191, 255),
    "dimgray": (105, 105, 105),
    "dimgrey": (105, 105, 105),
    "dodgerblue": (30, 144, 255),
    "firebrick": (178, 34, 34),
    "floralwhite": (255, 250, 240),
    "forestgreen": (34, 139, 34),
    "fuchsia": (255, 0, 255),
    "gainsboro": (220, 220, 220),
    "ghostwhite": (248, 248, 255),
    "gold": (255, 215, 0),
    "goldenrod": (218, 165, 32),
    "gray": (128, 128, 128),
    "green": (0, 128, 0),
    "greenyellow": (173, 255, 47),
    "grey": (128, 128, 128),
    "honeydew": (240, 255, 240),
    "hotpink": (255, 105, 180),
    "indianred": (205, 92, 92),
    "indigo": (75, 0, 130),
    "ivory": (255, 255, 240),
    "khaki": (240, 230, 140),
    "lavender": (230, 230, 250),
    "lavenderblush": (255, 240, 245),
    "lawngreen": (124, 252, 0),
    "lemonchiffon": (255, 250, 205),
    "lightblue": (173, 216, 230),
    "lightcoral": (240, 128, 128),
    "lightcyan": (224, 255, 255),
    "lightgoldenrodyellow": (250, 250, 210),
    "lightgray": (211, 211, 211),
    "lightgreen": (144, 238, 144),
    "lightgrey": (211, 211, 211),
    "lightpink": (255, 182, 193),
    "lightsalmon": (255, 160, 122),
    "lightseagreen": (32, 178, 170),
    "lightskyblue": (135, 206, 250),
    "lightslategray": (119, 136, 153),
    "lightslategrey": (119, 136, 153),
    "lightsteelblue": (176, 196, 222),
    "lightyellow": (255, 255, 224),
    "lime": (0, 255, 0),
    "limegreen": (50, 205, 50),
    "linen": (250, 240, 230),
    "magenta": (255, 0, 255),
    "maroon": (128, 0, 0),
    "mediumaquamarine": (102, 205, 170),
    "mediumblue": (0, 0, 205),
    "mediumorchid": (186, 85, 211),
    "mediumpurple": (147, 112, 219),
    "mediumseagreen": (60, 179, 113),
    "mediumslateblue": (123, 104, 238),
    "mediumspringgreen": (0, 250, 154),
    "mediumturquoise": (72, 209, 204),
    "mediumvioletred": (199, 21, 133),
    "midnightblue": (25, 25, 112),
    "mintcream": (245, 255, 250),
    "mistyrose": (255, 228, 225),
    "moccasin": (255, 228, 181),
    "navajowhite": (255, 222, 173),
    "navy": (0, 0, 128),
    "oldlace": (253, 245, 230),
    "olive": (128, 128, 0),
    "olivedrab": (107, 142, 35),
    "orange": (255, 165, 0),
    "orangered": (255, 69, 0),
    "orchid": (218, 112, 214),
    "palegoldenrod": (238, 232, 170),
    "palegreen": (152, 251, 152),
    "paleturquoise": (175, 238, 238),
    "palevioletred": (219, 112, 147),
    "papayawhip": (255, 239, 213),
    "peachpuff": (255, 218, 185),
    "peru": (205, 133, 63),
    "pink": (255, 192, 203),
    "plum": (221, 160, 221),
    "powderblue": (176, 224, 230),
    "purple": (128, 0, 128),
    "rebeccapurple": (102, 51, 153),
    "red": (255, 0, 0),
    "rosybrown": (188, 143, 143),
    "royalblue": (65, 105, 225),
    "saddlebrown": (139, 69, 19),
    "salmon": (250, 128, 114),
    "sandybrown": (244, 164, 96),
    "seagreen": (46, 139, 87),
    "seashell": (255, 245, 238),
    "sienna": (160, 82, 45),
    "silver": (192, 192, 192),
    "skyblue": (135, 206, 235),
    "slateblue": (106, 90, 205),
    "slategray": (112, 128, 144),
    "slategrey": (112, 128, 144),
    "snow": (255, 250, 250),
    "springgreen": (0, 255, 127),
    "steelblue": (70, 130, 180),
    "tan": (210, 180, 140),
    "teal": (0, 128, 128),
    "thistle": (216, 191, 216),
    "tomato": (255, 99, 71),
    "turquoise": (64, 224, 208),
    "violet": (238, 130, 238),
    "wheat": (245, 222, 179),
    "white": (255, 255, 255),
    "whitesmoke": (245, 245, 245),
    "yellow": (255, 255, 0),
    "yellowgreen": (154, 205, 50),
}


@dataclass(frozen=True)
class ColorMark:
    start: int
    length: int
    red: int
    green: int
    blue: int
    alpha: int
    kind: str
    text: str


def find_colors(text: str, named: bool = False) -> list[ColorMark]:
    """Return color literals. Offsets are UTF-8 bytes, matching the editor."""
    found: list[ColorMark] = []
    for match in _HEX.finditer(text):
        parsed = _hex_color(match.group(1))
        if parsed is None:
            continue
        red, green, blue, alpha = parsed
        found.append(_mark(text, match.start(), match.end(), red, green, blue, alpha, _hex_kind(match.group(1)), match.group(0)))
    for match in _FUNC.finditer(text):
        parsed = _func_color(match.group(1), match.group(2))
        if parsed is None:
            continue
        red, green, blue, alpha, kind = parsed
        found.append(_mark(text, match.start(), match.end(), red, green, blue, alpha, kind, match.group(0)))
    if named:
        for match in _NAME.finditer(text):
            rgb = _NAMED.get(match.group(1).casefold())
            if rgb is None:
                continue
            found.append(_mark(text, match.start(), match.end(), rgb[0], rgb[1], rgb[2], 255, "name", match.group(0)))
    found.sort(key=lambda item: item.start)
    kept: list[ColorMark] = []
    cursor = -1
    for item in found:
        if item.start < cursor:
            continue
        kept.append(item)
        cursor = item.start + item.length
    return kept


def recolor(mark: ColorMark, red: int, green: int, blue: int, alpha: int) -> str:
    """Write the same kind of literal with a new color."""
    red = _clamp(red)
    green = _clamp(green)
    blue = _clamp(blue)
    alpha = _clamp(alpha)
    if mark.kind == "hex3":
        return "#" + _short(red) + _short(green) + _short(blue)
    if mark.kind == "hex4":
        return "#" + _short(red) + _short(green) + _short(blue) + _short(alpha)
    if mark.kind == "hex8":
        return f"#{red:02x}{green:02x}{blue:02x}{alpha:02x}"
    if mark.kind == "rgb":
        return f"rgb({red}, {green}, {blue})"
    if mark.kind == "rgba":
        return f"rgba({red}, {green}, {blue}, {_alpha_text(mark.text, alpha)})"
    if mark.kind in {"hsl", "hsla"}:
        hue, sat, light = _rgb_to_hsl(red, green, blue)
        body = f"{hue}, {sat}%, {light}%"
        if mark.kind == "hsla":
            return f"hsla({body}, {_alpha_text(mark.text, alpha)})"
        return f"hsl({body})"
    return f"#{red:02x}{green:02x}{blue:02x}"


def _mark(text: str, start: int, end: int, red: int, green: int, blue: int, alpha: int, kind: str, raw: str) -> ColorMark:
    byte_start = len(text[:start].encode("utf-8"))
    byte_end = len(text[:end].encode("utf-8"))
    return ColorMark(byte_start, byte_end - byte_start, red, green, blue, alpha, kind, raw)


def _hex_kind(digits: str) -> str:
    return {3: "hex3", 4: "hex4", 6: "hex6", 8: "hex8"}[len(digits)]


def _hex_color(digits: str) -> tuple[int, int, int, int] | None:
    if len(digits) in {3, 4}:
        digits = "".join(char * 2 for char in digits)
    if len(digits) == 6:
        digits += "ff"
    if len(digits) != 8:
        return None
    try:
        red = int(digits[0:2], 16)
        green = int(digits[2:4], 16)
        blue = int(digits[4:6], 16)
        alpha = int(digits[6:8], 16)
    except ValueError:
        return None
    return red, green, blue, alpha


def _func_color(name: str, body: str) -> tuple[int, int, int, int, str] | None:
    kind = name.casefold()
    parts = [part.strip() for part in re.split(r"[,/\s]+", body) if part.strip()]
    if kind in {"rgb", "rgba"}:
        if len(parts) < 3:
            return None
        channels = [_channel(part) for part in parts[:3]]
        if any(item is None for item in channels):
            return None
        alpha = 255 if len(parts) < 4 else _alpha(parts[3])
        if alpha is None:
            return None
        return channels[0], channels[1], channels[2], alpha, "rgba" if kind == "rgba" or len(parts) > 3 else "rgb"
    if len(parts) < 3:
        return None
    hue = _number(parts[0].rstrip("deg"))
    sat = _percent(parts[1])
    light = _percent(parts[2])
    if hue is None or sat is None or light is None:
        return None
    red, green, blue = _hsl_to_rgb(hue % 360, sat, light)
    alpha = 255 if len(parts) < 4 else _alpha(parts[3])
    if alpha is None:
        return None
    return red, green, blue, alpha, "hsla" if kind == "hsla" or len(parts) > 3 else "hsl"


def _channel(text: str) -> int | None:
    if text.endswith("%"):
        value = _number(text[:-1])
        if value is None:
            return None
        return _clamp(round(value / 100 * 255))
    value = _number(text)
    if value is None:
        return None
    return _clamp(round(value))


def _percent(text: str) -> float | None:
    if not text.endswith("%"):
        return None
    value = _number(text[:-1])
    if value is None:
        return None
    return max(0.0, min(100.0, value)) / 100


def _alpha(text: str) -> int | None:
    if text.endswith("%"):
        value = _number(text[:-1])
        if value is None:
            return None
        return _clamp(round(value / 100 * 255))
    value = _number(text)
    if value is None:
        return None
    if "." in text or value <= 1:
        return _clamp(round(value * 255))
    return _clamp(round(value))


def _number(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def _alpha_text(original: str, alpha: int) -> str:
    if "." in original:
        return f"{alpha / 255:.2f}".rstrip("0").rstrip(".")
    return str(alpha)


def _short(value: int) -> str:
    snapped = min(15, round(_clamp(value) / 17))
    return f"{snapped:x}"


def _clamp(value: int) -> int:
    return max(0, min(255, int(value)))


def _hsl_to_rgb(hue: float, sat: float, light: float) -> tuple[int, int, int]:
    chroma = (1 - abs(2 * light - 1)) * sat
    sector = (hue / 60) % 2
    cross = chroma * (1 - abs(sector - 1))
    match = light - chroma / 2
    if hue < 60:
        red, green, blue = chroma, cross, 0.0
    elif hue < 120:
        red, green, blue = cross, chroma, 0.0
    elif hue < 180:
        red, green, blue = 0.0, chroma, cross
    elif hue < 240:
        red, green, blue = 0.0, cross, chroma
    elif hue < 300:
        red, green, blue = cross, 0.0, chroma
    else:
        red, green, blue = chroma, 0.0, cross
    return (
        _clamp(round((red + match) * 255)),
        _clamp(round((green + match) * 255)),
        _clamp(round((blue + match) * 255)),
    )


def _rgb_to_hsl(red: int, green: int, blue: int) -> tuple[int, int, int]:
    rf, gf, bf = red / 255, green / 255, blue / 255
    high = max(rf, gf, bf)
    low = min(rf, gf, bf)
    light = (high + low) / 2
    delta = high - low
    if delta == 0:
        hue = 0.0
        sat = 0.0
    else:
        sat = delta / (1 - abs(2 * light - 1))
        if high == rf:
            hue = 60 * (((gf - bf) / delta) % 6)
        elif high == gf:
            hue = 60 * (((bf - rf) / delta) + 2)
        else:
            hue = 60 * (((rf - gf) / delta) + 4)
    return round(hue) % 360, round(sat * 100), round(light * 100)
