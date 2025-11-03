import argparse
import random
import xml.etree.ElementTree as ET
from copy import deepcopy
from textwrap import dedent
from typing import Optional

VERTICAL_SPEED_FACTOR = 1.45

COLUMN_WAVE_GROUP = 6
COLUMN_PHASE_STEP = 0.45
COLUMN_SECONDARY_FACTOR = 0.18
COLUMN_RANDOM_JITTER = 0.16
MICRO_PHASE_SCALE = 0.6

BASE_CANVAS_WIDTH = 500.0
EDGE_MARGIN = 0.0
MIN_SPAN_WIDTH = BASE_CANVAS_WIDTH - 2 * EDGE_MARGIN
COLUMN_BASE_SPACING = 42.0

NICE_FEATURE_STEPS = [
    ("disable_font_size_animation", "Disable subtle per-glyph font-size pulsation."),
    ("disable_micro_jitter", "Disable the small additive transform jitters per glyph."),
    ("disable_per_glyph_opacity", "Disable per-glyph opacity pulsing."),
    ("disable_fill_opacity_pulse", "Disable fill-opacity shimmer on each glyph."),
    ("disable_trail_filter", "Remove the blur-based trail filter."),
    ("disable_lightning", "Remove the lightning overlay group."),
]

MAX_NICE_LEVEL = len(NICE_FEATURE_STEPS)

SVG_NS = "http://www.w3.org/2000/svg"
DC_NS = "http://purl.org/dc/elements/1.1/"
CC_NS = "http://creativecommons.org/ns#"
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

ET.register_namespace("dc", DC_NS)
ET.register_namespace("cc", CC_NS)
ET.register_namespace("rdf", RDF_NS)

STYLE_TEXT = dedent(
    """
    #matrixRain text {
      will-change: transform, opacity;
      transform-box: fill-box;
      transform-origin: center;
    }
    """
).strip()

TRAIL_COLOR_MATRIX_VALUES = dedent(
    """
    1 0 0 0 0
    0 1 0 0 0
    0 0 1 0 0
    0 0 0 0.6 0
    """
).strip()


def ns_tag(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


def indent(elem: ET.Element, level: int = 0) -> None:
    spacing = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = spacing + "  "
        for child in elem:
            indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = spacing + "  "
        if not elem[-1].tail or not elem[-1].tail.strip():
            elem[-1].tail = spacing
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = spacing


def build_metadata() -> ET.Element:
    metadata = ET.Element("metadata")
    rdf_root = ET.SubElement(metadata, ns_tag(RDF_NS, "RDF"))

    work = ET.SubElement(
        rdf_root,
        ns_tag(CC_NS, "Work"),
        {ns_tag(RDF_NS, "about"): ""},
    )
    ET.SubElement(work, ns_tag(DC_NS, "title")).text = "Matrix Rain Glyph Cascade"
    ET.SubElement(work, ns_tag(DC_NS, "creator")).text = "Shane Macaulay (K2)"
    ET.SubElement(work, ns_tag(DC_NS, "identifier")).text = "https://github.com/K2"
    ET.SubElement(
        work,
        ns_tag(DC_NS, "description"),
    ).text = (
        "Animated matrix-style glyph rainfall generated via DeepSeek-OCR assets pipeline."
    )
    ET.SubElement(
        work,
        ns_tag(DC_NS, "rights"),
    ).text = "© 2025 Shane Macaulay (K2) — Noncommercial use only. Contact ktwo@ktwo.ca."
    ET.SubElement(work, ns_tag(DC_NS, "language")).text = "en"
    ET.SubElement(
        work,
        ns_tag(CC_NS, "license"),
        {ns_tag(RDF_NS, "resource"): "https://creativecommons.org/licenses/by-nc/4.0/"},
    )

    license_elem = ET.SubElement(
        rdf_root,
        ns_tag(CC_NS, "License"),
        {ns_tag(RDF_NS, "about"): "https://creativecommons.org/licenses/by-nc/4.0/"},
    )
    for resource in (
        "https://creativecommons.org/ns#Reproduction",
        "https://creativecommons.org/ns#Distribution",
        "https://creativecommons.org/ns#DerivativeWorks",
    ):
        ET.SubElement(
            license_elem,
            ns_tag(CC_NS, "permits"),
            {ns_tag(RDF_NS, "resource"): resource},
        )
    ET.SubElement(
        license_elem,
        ns_tag(CC_NS, "requires"),
        {ns_tag(RDF_NS, "resource"): "https://creativecommons.org/ns#Attribution"},
    )
    ET.SubElement(
        license_elem,
        ns_tag(CC_NS, "prohibits"),
        {ns_tag(RDF_NS, "resource"): "https://creativecommons.org/ns#CommercialUse"},
    )
    return metadata


def build_style() -> ET.Element:
    style_elem = ET.Element("style")
    style_elem.text = "\n" + STYLE_TEXT + "\n"
    return style_elem


def build_defs() -> ET.Element:
    defs = ET.Element("defs")

    grad_glow = ET.SubElement(
        defs,
        "linearGradient",
        {"id": "gradGlow", "gradientUnits": "userSpaceOnUse", "x1": "0", "y1": "0", "x2": "0", "y2": "500"},
    )
    ET.SubElement(grad_glow, "stop", {"offset": "0%", "stop-color": "#9AFF9A"})
    ET.SubElement(grad_glow, "stop", {"offset": "60%", "stop-color": "#31FF6B"})
    ET.SubElement(grad_glow, "stop", {"offset": "100%", "stop-color": "#00BF47"})

    grad_bolt = ET.SubElement(
        defs,
        "linearGradient",
        {"id": "gradBolt", "gradientUnits": "userSpaceOnUse", "x1": "0", "y1": "0", "x2": "0", "y2": "500"},
    )
    ET.SubElement(grad_bolt, "stop", {"offset": "0%", "stop-color": "#FFB347"})
    ET.SubElement(grad_bolt, "stop", {"offset": "60%", "stop-color": "#FF6A00"})
    ET.SubElement(grad_bolt, "stop", {"offset": "100%", "stop-color": "#FF2400"})

    soft_glow = ET.SubElement(
        defs,
        "filter",
        {"id": "softGlow", "x": "-40%", "y": "-40%", "width": "180%", "height": "180%"},
    )
    ET.SubElement(soft_glow, "feGaussianBlur", {"stdDeviation": "2.2", "result": "blur"})
    merge = ET.SubElement(soft_glow, "feMerge")
    ET.SubElement(merge, "feMergeNode", {"in": "blur"})
    ET.SubElement(merge, "feMergeNode", {"in": "SourceGraphic"})

    trail_glow = ET.SubElement(
        defs,
        "filter",
        {"id": "trailGlow", "x": "-40%", "y": "-40%", "width": "180%", "height": "220%"},
    )
    ET.SubElement(
        trail_glow,
        "feGaussianBlur",
        {"in": "SourceGraphic", "stdDeviation": "0 7", "result": "trail"},
    )
    ET.SubElement(
        trail_glow,
        "feColorMatrix",
        {"in": "trail", "type": "matrix", "values": TRAIL_COLOR_MATRIX_VALUES, "result": "trailFade"},
    )
    trail_merge = ET.SubElement(trail_glow, "feMerge")
    ET.SubElement(trail_merge, "feMergeNode", {"in": "trailFade"})
    ET.SubElement(trail_merge, "feMergeNode", {"in": "SourceGraphic"})

    vignette = ET.SubElement(
        defs,
        "radialGradient",
        {"id": "vignette", "cx": "50%", "cy": "50%", "r": "65%"},
    )
    ET.SubElement(vignette, "stop", {"offset": "0%", "stop-color": "rgba(0,0,0,0)"})
    ET.SubElement(vignette, "stop", {"offset": "100%", "stop-color": "rgba(0,0,0,0.55)"})

    flash_glow = ET.SubElement(
        defs,
        "radialGradient",
        {"id": "flashGlow", "cx": "50%", "cy": "50%", "r": "75%"},
    )
    ET.SubElement(
        flash_glow,
        "stop",
        {"offset": "0%", "stop-color": "#FFB347", "stop-opacity": "0.85"},
    )
    ET.SubElement(
        flash_glow,
        "stop",
        {"offset": "55%", "stop-color": "#FF5F1F", "stop-opacity": "0.45"},
    )
    ET.SubElement(
        flash_glow,
        "stop",
        {"offset": "100%", "stop-color": "#FF2400", "stop-opacity": "0"},
    )

    return defs


def add_background_rects(svg_root: ET.Element, canvas_width: float) -> None:
    width_text = fmt_num(canvas_width)
    ET.SubElement(
        svg_root,
        "rect",
        {"x": "0", "y": "0", "width": width_text, "height": "500", "fill": "#050507"},
    )
    ET.SubElement(
        svg_root,
        "rect",
        {"x": "0", "y": "0", "width": width_text, "height": "500", "fill": "url(#vignette)"},
    )


LIGHTNING_POINTS_BASE = [
    (250, -60),
    (262, 80),
    (242, 170),
    (260, 260),
    (238, 360),
    (252, 480),
    (246, 560),
]


def build_lightning(canvas_width: float) -> ET.Element:
    width_scale = canvas_width / BASE_CANVAS_WIDTH if BASE_CANVAS_WIDTH else 1.0
    points = " ".join(
        f"{fmt_num(x * width_scale)},{fmt_num(y)}" for x, y in LIGHTNING_POINTS_BASE
    )

    lightning = ET.Element("g", {"id": "lightning", "pointer-events": "none"})

    rect = ET.SubElement(
        lightning,
        "rect",
        {
            "x": "0",
            "y": "0",
            "width": fmt_num(canvas_width),
            "height": "500",
            "fill": "url(#flashGlow)",
            "opacity": "0",
        },
    )
    ET.SubElement(
        rect,
        "animate",
        {
            "attributeName": "opacity",
            "values": "0;0;0.88;0",
            "keyTimes": "0;0.8;0.84;1",
            "dur": "12s",
            "repeatCount": "indefinite",
        },
    )

    polyline = ET.SubElement(
        lightning,
        "polyline",
        {
            "points": points,
            "stroke": "url(#gradBolt)",
            "stroke-width": "12",
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            "fill": "none",
            "opacity": "0",
            "filter": "url(#softGlow)",
        },
    )
    ET.SubElement(
        polyline,
        "animate",
        {
            "attributeName": "opacity",
            "values": "0;0;1;0",
            "keyTimes": "0;0.82;0.86;1",
            "dur": "12s",
            "repeatCount": "indefinite",
        },
    )
    ET.SubElement(
        polyline,
        "animate",
        {
            "attributeName": "stroke-width",
            "values": "12;16;12",
            "dur": "12s",
            "begin": "-0.4s",
            "repeatCount": "indefinite",
        },
    )
    ET.SubElement(
        polyline,
        "animate",
        {
            "attributeName": "stroke-dashoffset",
            "values": "0;-140;0",
            "dur": "0.9s",
            "repeatCount": "indefinite",
        },
    )

    return lightning


def resolve_nice_flags(requested_level: int):
    """Clamp the requested nice level and derive which features to disable."""

    level = max(0, min(requested_level, MAX_NICE_LEVEL))
    flags = {name: False for name, _ in NICE_FEATURE_STEPS}

    for idx, (name, _description) in enumerate(NICE_FEATURE_STEPS, start=1):
        if level >= idx:
            flags[name] = True

    return level, flags

patterns = [
    {
        "fill_values": "0.3;0.95;0.3",
        "fill_dur": 2.6,
        "fill_begin": -0.9,
        "transform_values": "0,-8;0,4;0,-5;0,-8",
        "transform_dur": 3.4,
        "transform_begin": -0.5,
        "size_dur": 4.0,
        "size_begin": -1.1,
        "size_high": 1.0,
        "size_low": -1.0,
    },
    {
        "fill_values": "0.25;0.88;0.28;0.25",
        "fill_dur": 2.2,
        "fill_begin": -1.6,
        "transform_values": "0,-6;0,2;0,-4;0,-6",
        "transform_dur": 2.9,
        "transform_begin": -0.7,
        "size_dur": 3.3,
        "size_begin": -0.8,
        "size_high": 1.2,
        "size_low": -0.8,
    },
    {
        "fill_values": "0.2;0.92;0.2",
        "fill_dur": 3.1,
        "fill_begin": -0.4,
        "transform_values": "0,-10;0,5;0,-3;0,-10",
        "transform_dur": 3.6,
        "transform_begin": -1.2,
        "size_dur": 3.7,
        "size_begin": -1.4,
        "size_high": 0.8,
        "size_low": -1.2,
    },
    {
        "fill_values": "0.34;0.9;0.34",
        "fill_dur": 2.4,
        "fill_begin": -1.2,
        "transform_values": "0,-7;0,3;0,-6;0,-7",
        "transform_dur": 3.0,
        "transform_begin": -0.3,
        "size_dur": 3.5,
        "size_begin": -1.0,
        "size_high": 1.0,
        "size_low": -0.5,
    },
    {
        "fill_values": "0.18;0.82;0.24;0.18",
        "fill_dur": 4.8,
        "fill_begin": -2.1,
        "transform_values": "0,-5;0,6;0,-7;0,-5",
        "transform_dur": 6.3,
        "transform_begin": -1.8,
        "size_dur": 4.9,
        "size_begin": -2.2,
        "size_high": 1.6,
        "size_low": -1.3,
    },
    {
        "fill_values": "0.4;1;0.5;0.4",
        "fill_dur": 1.7,
        "fill_begin": -0.65,
        "transform_values": "0,-14;0,3;0,-9;0,-14",
        "transform_dur": 2.1,
        "transform_begin": -0.95,
        "size_dur": 2.4,
        "size_begin": -0.7,
        "size_high": 0.6,
        "size_low": -1.8,
    },
    {
        "fill_values": "0.22;0.9;0.3;0.22",
        "fill_dur": 5.6,
        "fill_begin": -2.8,
        "transform_values": "0,-6;0,5;0,-8;0,-6",
        "transform_dur": 6.8,
        "transform_begin": -2.4,
        "size_dur": 5.4,
        "size_begin": -2.6,
        "size_high": 1.8,
        "size_low": -1.5,
    },
    {
        "fill_values": "0.32;0.96;0.4;0.32",
        "fill_dur": 1.4,
        "fill_begin": -0.35,
        "transform_values": "0,-18;0,8;0,-11;0,-18",
        "transform_dur": 1.9,
        "transform_begin": -0.55,
        "size_dur": 2.1,
        "size_begin": -0.6,
        "size_high": 0.9,
        "size_low": -2.1,
    },
]

base_columns = [
    {
        "x": 20,
        "translate_values": "0,-260;0,540",
        "translate_dur": 4.2,
        "translate_begin": -1.4,
        "opacity_values": "0.2;0.95;0.2",
        "opacity_dur": 4.2,
        "opacity_begin": -1.4,
        "glyphs": [("A", 18), ("Σ", 20), ("7", 21), ("Ω", 19), ("Ñ", 18), ("@", 21), ("Z", 23), ("É", 19), ("?", 18), ("δ", 17), ("∞", 20)],
    },
    {
        "x": 60,
        "translate_values": "0,-300;0,520",
        "translate_dur": 5.1,
        "translate_begin": -0.8,
        "opacity_values": "0.18;1;0.18",
        "opacity_dur": 5.1,
        "opacity_begin": -0.8,
        "glyphs": [("ß", 18), ("M", 21), ("鶴", 22), ("λ", 19), ("Ü", 18), ("鶴", 20), ("Q", 23), ("ß", 19), ("3", 18), ("η", 17), ("≈", 20)],
    },
    {
        "x": 100,
        "translate_values": "0,-240;0,520",
        "translate_dur": 4.7,
        "translate_begin": -2.3,
        "opacity_values": "0.25;0.9;0.25",
        "opacity_dur": 4.7,
        "opacity_begin": -2.3,
        "glyphs": [("C", 18), ("S", 20), ("%", 22), ("Ψ", 19), ("Í", 17), ("5", 21), ("T", 23), ("χ", 19), ("8", 18), ("κ", 17), ("∈", 20)],
    },
    {
        "x": 140,
        "translate_values": "0,-320;0,520",
        "translate_dur": 5.4,
        "translate_begin": -0.4,
        "opacity_values": "0.18;0.92;0.18",
        "opacity_dur": 5.4,
        "opacity_begin": -0.4,
        "glyphs": [("D", 18), ("L", 21), ("$", 22), ("β", 19), ("Ó", 17), ("1", 21), ("P", 23), ("Ξ", 19), ("6", 18), ("ϑ", 17), ("∮", 20)],
    },
    {
        "x": 180,
        "translate_values": "0,-260;0,560",
        "translate_dur": 4.1,
        "translate_begin": -1.9,
        "opacity_values": "0.26;0.9;0.26",
        "opacity_dur": 4.1,
        "opacity_begin": -1.9,
        "glyphs": [("E", 18), ("V", 21), ("0", 22), ("Γ", 19), ("Ú", 17), ("2", 21), ("F", 23), ("Ζ", 19), ("4", 18), ("θ", 17), ("∟", 20)],
    },
    {
        "x": 220,
        "translate_values": "0,-300;0,560",
        "translate_dur": 5.8,
        "translate_begin": -3.2,
        "opacity_values": "0.17;0.95;0.17",
        "opacity_dur": 5.8,
        "opacity_begin": -3.2,
        "glyphs": [("F", 18), ("X", 21), ("!", 22), ("Φ", 19), ("Å", 17), ("%", 21), ("N", 23), ("Π", 19), ("œ", 18), ("μ", 17), ("∴", 20)],
    },
    {
        "x": 260,
        "translate_values": "0,-260;0,520",
        "translate_dur": 4.4,
        "translate_begin": -0.2,
        "opacity_values": "0.24;0.93;0.24",
        "opacity_dur": 4.4,
        "opacity_begin": -0.2,
        "glyphs": [("G", 18), ("Y", 21), ("@", 22), ("Υ", 19), ("Í", 17), ("ρ", 21), ("Æ", 23), ("W", 19), ("ħ", 18), ("ξ", 17), ("∠", 20)],
    },
    {
        "x": 300,
        "translate_values": "0,-280;0,560",
        "translate_dur": 5.0,
        "translate_begin": -1.1,
        "opacity_values": "0.2;0.97;0.2",
        "opacity_dur": 5.0,
        "opacity_begin": -1.1,
        "glyphs": [("ñ", 18), ("T", 21), ("8", 22), ("ϖ", 19), ("Ê", 17), ("σ", 21), ("Ğ", 23), ("V", 19), ("ň", 18), ("ς", 17), ("∵", 20)],
    },
    {
        "x": 340,
        "translate_values": "0,-240;0,520",
        "translate_dur": 4.3,
        "translate_begin": -2.7,
        "opacity_values": "0.22;0.92;0.22",
        "opacity_dur": 4.3,
        "opacity_begin": -2.7,
        "glyphs": [("I", 18), ("P", 21), ("6", 22), ("ϱ", 19), ("Ë", 17), ("ϙ", 21), ("Ð", 23), ("U", 19), ("ŕ", 18), ("Ϟ", 17), ("∗", 20)],
    },
    {
        "x": 380,
        "translate_values": "0,-320;0,560",
        "translate_dur": 5.6,
        "translate_begin": -1.5,
        "opacity_values": "0.19;0.96;0.19",
        "opacity_dur": 5.6,
        "opacity_begin": -1.5,
        "glyphs": [("¿", 18), ("N", 21), ("5", 22), ("ϗ", 19), ("Ę", 17), ("ϛ", 21), ("Ç", 23), ("R", 19), ("ś", 18), ("ϟ", 17), ("∯", 20)],
    },
    {
        "x": 420,
        "translate_values": "0,-260;0,520",
        "translate_dur": 4.5,
        "translate_begin": -0.9,
        "opacity_values": "0.24;0.9;0.24",
        "opacity_dur": 4.5,
        "opacity_begin": -0.9,
        "glyphs": [("K", 18), ("C", 21), ("4", 22), ("Ϥ", 19), ("Ě", 17), ("ϝ", 21), ("Ō", 23), ("S", 19), ("ž", 18), ("ϡ", 17), ("∼", 20)],
    },
    {
        "x": 460,
        "translate_values": "0,-300;0,560",
        "translate_dur": 5.2,
        "translate_begin": -2.5,
        "opacity_values": "0.21;0.94;0.21",
        "opacity_dur": 5.2,
        "opacity_begin": -2.5,
        "glyphs": [("ψ", 18), ("E", 21), ("3", 22), ("Θ", 19), ("Á", 17), ("Δ", 21), ("Š", 23), ("T", 19), ("ñ", 18), ("β", 17), ("⊕", 20)],
    },
]

extra_glyph_cycle = [
    ("ß", 19),
    ("ø", 20),
    ("Σ", 22),
    ("ñ", 18),
    ("#", 19),
    ("ξ", 18),
    ("Þ", 21),
    ("¡", 19),
    ("ψ", 21),
    ("Ł", 20),
    ("¿", 19),
    ("K", 21),
    ("κ", 20),
    ("Ϟ", 22),
    ("2", 21),
    ("0", 21),
    ("Ω", 22),
]

K2_GLYPH = ("K2", 22)
KTWO_GLYPH = ("ktwo", 20)
ASSISTANT_GLYPH = ("∑AI", 20)
SIGNATURE_GLYPHS = [K2_GLYPH, KTWO_GLYPH]


def fmt_num(value: float) -> str:
    text = f"{value:.2f}"
    if text.endswith("00"):
        return text[:-3]
    return text.rstrip("0").rstrip(".")


def generate_glyph_sequence(column_seed: int, base_glyphs, target_count: int):
    """Expand or trim the glyph list to the desired count deterministically."""

    if target_count <= 0:
        return []

    glyphs = list(base_glyphs[:target_count])
    if len(glyphs) == target_count:
        return glyphs

    extended_cycle = list(extra_glyph_cycle)

    if column_seed % 11 == 0:
        extended_cycle.insert(0, ASSISTANT_GLYPH)
    if column_seed % 5 == 0:
        extended_cycle.insert(0, K2_GLYPH)
    elif column_seed % 7 == 0:
        extended_cycle.insert(0, KTWO_GLYPH)

    cycle_len = len(extended_cycle)
    rotation = (column_seed * 3) % cycle_len
    rotated_cycle = [extended_cycle[(rotation + i) % cycle_len] for i in range(cycle_len)]

    cycle_idx = 0
    while len(glyphs) < target_count:
        glyphs.append(rotated_cycle[cycle_idx % cycle_len])
        cycle_idx += 1

    return glyphs


irregular_offsets = [12, 53, 97, 141, 176, 219, 263, 298, 336, 371, 413, 452]
phase_shifts = [0.85, -0.6, 1.4, -1.15, 0.32, 1.92, -0.78, 1.28, -0.42, 0.96, -1.48, 1.61]
translate_scales = [1.18, 0.82, 1.35, 0.87, 1.26, 0.79, 1.32, 0.9, 1.24, 0.84, 1.29, 0.93]
opacity_scales = [1.12, 0.86, 1.3, 0.9, 1.18, 0.82, 1.24, 0.88, 1.16, 0.84, 1.22, 0.9]


def build_matrix_rain(columns, nice_flags) -> ET.Element:
    rain_group = ET.Element(
        "g",
        {
            "id": "matrixRain",
            "opacity": "0.95",
            "font-family": "system-ui, sans-serif",
            "letter-spacing": "2",
        },
    )

    for col_idx, col in enumerate(columns):
        column_group = ET.SubElement(
            rain_group,
            "g",
            {"transform": f'translate({fmt_num(col["x"])},0)'},
        )
        inner_attrs = {}
        if not nice_flags["disable_trail_filter"]:
            inner_attrs["filter"] = "url(#trailGlow)"
        column_inner = ET.SubElement(column_group, "g", inner_attrs)

        translate_pairs = [
            tuple(map(float, pair.split(','))) for pair in col["translate_values"].split(';')
        ]
        start_offset_y = translate_pairs[0][1]
        end_offset_y = translate_pairs[-1][1]

        column_wave_base = (col_idx % COLUMN_WAVE_GROUP) * COLUMN_PHASE_STEP
        column_wave_secondary = (col_idx // COLUMN_WAVE_GROUP) * COLUMN_PHASE_STEP * COLUMN_SECONDARY_FACTOR
        column_wave_jitter = (((col_idx * 0.61803398875) % 1.0) - 0.5) * COLUMN_RANDOM_JITTER
        column_anchor = column_wave_base + column_wave_secondary + column_wave_jitter

        for glyph_idx, (char, size) in enumerate(col["glyphs"]):
            base_y = 20 + glyph_idx * 40
            pattern_idx = (glyph_idx + col_idx) % len(patterns)
            pattern = patterns[pattern_idx]
            micro_phase = (col_idx * 0.18 + glyph_idx * 0.07) * MICRO_PHASE_SCALE

            start_y = base_y + start_offset_y
            end_y = base_y + end_offset_y
            start_translation = start_y - base_y
            end_translation = end_y - base_y

            fill_begin = pattern["fill_begin"] + column_anchor - micro_phase
            jitter_begin = pattern["transform_begin"] + column_anchor - micro_phase * 0.8
            size_begin = pattern["size_begin"] + column_anchor - micro_phase * 0.5
            opacity_begin = col["opacity_begin"] + column_anchor - micro_phase * 0.6

            fall_scale = 0.95 + 0.08 * (glyph_idx % 5) + 0.05 * (pattern_idx % 3)
            fall_dur = col["translate_dur"] * fall_scale * VERTICAL_SPEED_FACTOR
            fall_begin = col["translate_begin"] + column_anchor - micro_phase

            opacity_scale = 0.9 + 0.04 * ((glyph_idx + 2 * col_idx) % 4)
            opacity_dur = col["opacity_dur"] * opacity_scale

            scale_high = (size + pattern["size_high"]) / size if size else 1.0
            scale_low = (size + pattern["size_low"]) / size if size else 1.0
            scale_high = max(scale_high, 0.2)
            scale_low = max(scale_low, 0.2)
            scale_values = ";".join(
                fmt_num(value) for value in (1.0, scale_high, scale_low, 1.0)
            )

            opacity_values = col["opacity_values"].split(';')
            peak_opacity = min(
                0.98,
                max(
                    0.4,
                    float(opacity_values[1])
                    * (1.0 + 0.08 * ((glyph_idx % 3) - 1)),
                ),
            )
            per_glyph_opacity = ";".join(
                (fmt_num(0.08), fmt_num(peak_opacity), fmt_num(0.06))
            )

            fill_values_sequence = [
                float(value) for value in pattern["fill_values"].split(';')
            ]
            fill_static = fmt_num(sum(fill_values_sequence) / len(fill_values_sequence))

            text_attrs = {
                "x": "0",
                "y": fmt_num(base_y),
                "fill": "url(#gradGlow)",
                "font-size": fmt_num(size),
                "transform": f'translate(0,{fmt_num(start_translation)})',
            }

            if nice_flags["disable_per_glyph_opacity"]:
                text_attrs["opacity"] = fmt_num(peak_opacity)

            if nice_flags["disable_fill_opacity_pulse"]:
                text_attrs["fill-opacity"] = fill_static

            text_elem = ET.SubElement(column_inner, "text", text_attrs)
            text_elem.text = char

            ET.SubElement(
                text_elem,
                "animateTransform",
                {
                    "attributeName": "transform",
                    "type": "translate",
                    "values": f'0,{fmt_num(start_translation)};0,{fmt_num(end_translation)}',
                    "dur": f"{fmt_num(fall_dur)}s",
                    "begin": f"{fmt_num(fall_begin)}s",
                    "repeatCount": "indefinite",
                },
            )

            if not nice_flags["disable_fill_opacity_pulse"]:
                ET.SubElement(
                    text_elem,
                    "animate",
                    {
                        "attributeName": "fill-opacity",
                        "values": pattern["fill_values"],
                        "dur": f"{fmt_num(pattern['fill_dur'])}s",
                        "begin": f"{fmt_num(fill_begin)}s",
                        "repeatCount": "indefinite",
                    },
                )

            if not nice_flags["disable_per_glyph_opacity"]:
                ET.SubElement(
                    text_elem,
                    "animate",
                    {
                        "attributeName": "opacity",
                        "values": per_glyph_opacity,
                        "dur": f"{fmt_num(opacity_dur)}s",
                        "begin": f"{fmt_num(opacity_begin)}s",
                        "repeatCount": "indefinite",
                    },
                )

            if not nice_flags["disable_font_size_animation"]:
                ET.SubElement(
                    text_elem,
                    "animateTransform",
                    {
                        "attributeName": "transform",
                        "type": "scale",
                        "values": scale_values,
                        "dur": f"{fmt_num(pattern['size_dur'])}s",
                        "begin": f"{fmt_num(size_begin)}s",
                        "repeatCount": "indefinite",
                        "additive": "sum",
                    },
                )

            if not nice_flags["disable_micro_jitter"]:
                ET.SubElement(
                    text_elem,
                    "animateTransform",
                    {
                        "attributeName": "transform",
                        "type": "translate",
                        "values": pattern["transform_values"],
                        "dur": f"{fmt_num(pattern['transform_dur'])}s",
                        "begin": f"{fmt_num(jitter_begin)}s",
                        "repeatCount": "indefinite",
                        "additive": "sum",
                    },
                )

    return rain_group


def build_columns(min_gps: int, max_gps: int, regular_count: int, irregular_count: int):
    rng = random.Random(0xC0FFEE)
    columns = []
    base_len = len(base_columns)
    irregular_len = len(irregular_offsets)
    total_columns = max(regular_count + irregular_count, 1)

    span_width = max(MIN_SPAN_WIDTH, (total_columns - 1) * COLUMN_BASE_SPACING)

    def pick_glyph_target() -> int:
        if min_gps == max_gps:
            return min_gps
        return rng.randint(min_gps, max_gps)

    for idx in range(max(0, regular_count)):
        template = deepcopy(base_columns[idx % base_len])
        if regular_count == 1:
            template["x"] = span_width / 2
        else:
            template["x"] = (span_width / max(regular_count - 1, 1)) * idx
        target_count = pick_glyph_target()
        template["glyphs"] = generate_glyph_sequence(idx, template["glyphs"], target_count)
        columns.append(template)

    offset_min = min(irregular_offsets) if irregular_offsets else 0.0
    offset_max = max(irregular_offsets) if irregular_offsets else 1.0

    def select_irregular_indices(count: int) -> list[int]:
        if count <= 0 or irregular_len == 0:
            return []
        if count == 1:
            return [irregular_len // 2]
        if count <= irregular_len:
            step = (irregular_len - 1) / (count - 1)
            indices: list[int] = []
            used: set[int] = set()
            for i in range(count):
                idx = int(round(i * step))
                idx = max(0, min(irregular_len - 1, idx))
                while idx in used and idx < irregular_len - 1:
                    idx += 1
                if idx in used:
                    candidate = idx - 1
                    while candidate >= 0 and candidate in used:
                        candidate -= 1
                    if candidate >= 0:
                        idx = candidate
                    else:
                        idx = (idx + 1) % irregular_len
                        while idx in used:
                            idx = (idx + 1) % irregular_len
                used.add(idx)
                indices.append(idx)
            return sorted(indices)
        # count > irregular_len, repeat with rotation for variety
        indices = []
        cycles = (count + irregular_len - 1) // irregular_len
        for cycle in range(cycles):
            offset = (cycle * 3) % irregular_len
            for pos in range(irregular_len):
                idx = (pos + offset) % irregular_len
                indices.append(idx)
                if len(indices) == count:
                    return indices
        return indices

    irregular_indices = select_irregular_indices(max(0, irregular_count))

    for idx, offset_idx in enumerate(irregular_indices):
        template = deepcopy(base_columns[idx % base_len])
        if offset_max == offset_min:
            normalized = 0.5
        else:
            normalized = (irregular_offsets[offset_idx] - offset_min) / (offset_max - offset_min)
        template["x"] = normalized * span_width
        shift = phase_shifts[offset_idx]
        template["translate_begin"] += shift
        template["opacity_begin"] += shift * 0.65
        template["translate_dur"] *= translate_scales[offset_idx]
        template["opacity_dur"] *= opacity_scales[offset_idx]
        target_count = pick_glyph_target()
        template["glyphs"] = generate_glyph_sequence(idx + regular_count, template["glyphs"], target_count)
        columns.append(template)

    if columns:
        xs = [col["x"] for col in columns]
        min_x = min(xs)
        max_x = max(xs)
        if max_x == min_x:
            normalized_positions = [span_width / 2.0 for _ in xs]
        else:
            scale = span_width / (max_x - min_x)
            normalized_positions = [(x - min_x) * scale for x in xs]
        for col, new_x in zip(columns, normalized_positions):
            col["x"] = new_x + EDGE_MARGIN
        canvas_width = span_width + 2 * EDGE_MARGIN
    else:
        canvas_width = BASE_CANVAS_WIDTH

    return columns, canvas_width


def build_svg(
    include_lightning: bool = True,
    nice_level: int = 0,
    gps_min: int = 22,
    gps_max: int = 22,
    regular_columns: Optional[int] = None,
    irregular_columns: Optional[int] = None,
    include_metadata: bool = True,
) -> str:
    nice_level, nice_flags = resolve_nice_flags(nice_level)

    gps_min = max(1, gps_min)
    gps_max = max(gps_min, gps_max)

    if regular_columns is None:
        regular_columns = len(base_columns)
    if irregular_columns is None:
        irregular_columns = len(base_columns)

    regular_columns = max(0, regular_columns)
    irregular_columns = max(0, irregular_columns)

    columns, canvas_width = build_columns(gps_min, gps_max, regular_columns, irregular_columns)
    include_lightning = include_lightning and not nice_flags["disable_lightning"]

    width_text = fmt_num(canvas_width)
    svg_attrs = {
        "xmlns": SVG_NS,
        "width": width_text,
        "height": "500",
        "viewBox": f"0 0 {width_text} 500",
        "style": "width:100%;height:auto;",
        "aria-label": "Animated neon glyph waterfall",
        "role": "img",
        "focusable": "true",
    }

    svg_root = ET.Element("svg", svg_attrs)
    if include_metadata:
        svg_root.append(build_metadata())
    svg_root.append(build_style())
    svg_root.append(build_defs())
    add_background_rects(svg_root, canvas_width)
    svg_root.append(build_matrix_rain(columns, nice_flags))
    if include_lightning:
        svg_root.append(build_lightning(canvas_width))

    indent(svg_root)
    return ET.tostring(svg_root, encoding="unicode")


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Generate the animated matrix rain SVG (base canvas width {:.0f} with adaptive span)."
            .format(BASE_CANVAS_WIDTH)
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    defaults_text = (
        "Defaults → glyphs per strand: {gps} min/max, regular columns: {reg}, irregular columns: {irr}, "
        "vertical speed factor: {vsf}."
    ).format(
        gps=22,
        reg=len(base_columns),
        irr=len(base_columns),
        vsf=fmt_num(VERTICAL_SPEED_FACTOR),
    )
    nice_lines = ["  0: keep all visual effects active"]
    nice_lines.extend(
        f"  {idx}: {desc}"
        for idx, (_name, desc) in enumerate(NICE_FEATURE_STEPS, start=1)
    )
    parser.epilog = defaults_text + "\nNice levels disable:\n" + "\n".join(nice_lines)
    parser.add_argument(
        "--no-lightning",
        action="store_true",
        help="Omit the lightning overlay from the generated SVG.",
    )
    parser.add_argument(
        "--nice",
        type=int,
        default=0,
        help=(
            "Performance dial. Each increment disables an additional effect, starting with subtle ones "
            "(levels 0 to {max_level})."
        ).format(max_level=MAX_NICE_LEVEL),
    )
    parser.add_argument(
        "--gps-min",
        type=int,
        default=22,
        help="Minimum glyphs per strand (per column).",
    )
    parser.add_argument(
        "--gps-max",
        type=int,
        default=22,
        help="Maximum glyphs per strand (per column).",
    )
    parser.add_argument(
        "--columns-regular",
        type=int,
        default=len(base_columns),
        help="Number of evenly spaced columns to include.",
    )
    parser.add_argument(
        "--columns-irregular",
        type=int,
        default=len(base_columns),
        help="Number of irregularly offset columns to include.",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Skip embedding the RDF/DC metadata block in the SVG output.",
    )

    args = parser.parse_args()

    if args.nice < 0:
        parser.error("--nice must be >= 0")
    if args.gps_min < 1:
        parser.error("--gps-min must be >= 1")
    if args.gps_max < args.gps_min:
        parser.error("--gps-max must be >= --gps-min")
    if args.columns_regular < 0:
        parser.error("--columns-regular must be >= 0")
    if args.columns_irregular < 0:
        parser.error("--columns-irregular must be >= 0")

    return args


def main():
    args = parse_args()
    svg = build_svg(
        include_lightning=not args.no_lightning,
        nice_level=args.nice,
        gps_min=args.gps_min,
        gps_max=args.gps_max,
        regular_columns=args.columns_regular,
        irregular_columns=args.columns_irregular,
        include_metadata=not args.no_metadata,
    )
    print(svg)


if __name__ == "__main__":
    main()
