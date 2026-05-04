"""OXML direct manipulation for effects not exposed by python-pptx API."""
from lxml import etree
from pptx.util import Pt
from pptx.dml.color import RGBColor


_NSMAP = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

def _a(tag: str) -> str:
    return f"{{{_NSMAP['a']}}}{tag}"


def _hex_to_rgb_str(hex_color: str) -> str:
    return hex_color.lstrip("#").upper()


def gradient_fill(shape, stops: list[tuple[int, str]], angle_deg: int = 90) -> None:
    """Apply a linear gradient fill to a shape via OXML.

    stops: list of (position_pct 0-100, hex_color)
    """
    sp = shape._element
    spPr = sp.find(_a("spPr"))
    if spPr is None:
        spPr = etree.SubElement(sp, _a("spPr"))

    # Remove existing fill
    for tag in [_a("noFill"), _a("solidFill"), _a("gradFill"), _a("pattFill")]:
        existing = spPr.find(tag)
        if existing is not None:
            spPr.remove(existing)

    gradFill = etree.SubElement(spPr, _a("gradFill"))
    gsLst = etree.SubElement(gradFill, _a("gsLst"))

    for pos_pct, hex_color in stops:
        gs = etree.SubElement(gsLst, _a("gs"), pos=str(pos_pct * 1000))
        solidFill = etree.SubElement(gs, _a("solidFill"))
        srgbClr = etree.SubElement(solidFill, _a("srgbClr"), val=_hex_to_rgb_str(hex_color))

    lin = etree.SubElement(gradFill, _a("lin"),
                           ang=str(int(angle_deg * 60000)),
                           scaled="0")


def solid_fill_shape(shape, hex_color: str) -> None:
    """Apply a solid fill to a shape."""
    sp = shape._element
    spPr = sp.find(_a("spPr"))
    if spPr is None:
        spPr = etree.SubElement(sp, _a("spPr"))

    for tag in [_a("noFill"), _a("solidFill"), _a("gradFill")]:
        existing = spPr.find(tag)
        if existing is not None:
            spPr.remove(existing)

    solidFill = etree.SubElement(spPr, _a("solidFill"))
    etree.SubElement(solidFill, _a("srgbClr"), val=_hex_to_rgb_str(hex_color))


def outer_shadow(shape, blur_pt: int = 8, dist_pt: int = 4,
                 angle_deg: int = 45, color_hex: str = "#000000",
                 alpha_pct: int = 25) -> None:
    """Add outer drop shadow to a shape."""
    sp = shape._element
    spPr = sp.find(_a("spPr"))
    if spPr is None:
        spPr = etree.SubElement(sp, _a("spPr"))

    effectLst = spPr.find(_a("effectLst"))
    if effectLst is None:
        effectLst = etree.SubElement(spPr, _a("effectLst"))

    # Remove existing shadow
    existing = effectLst.find(_a("outerShdw"))
    if existing is not None:
        effectLst.remove(existing)

    outerShdw = etree.SubElement(effectLst, _a("outerShdw"),
                                  blurRad=str(Pt(blur_pt).emu),
                                  dist=str(Pt(dist_pt).emu),
                                  dir=str(int(angle_deg * 60000)),
                                  algn="tl",
                                  rotWithShape="0")
    srgbClr = etree.SubElement(outerShdw, _a("srgbClr"),
                                val=_hex_to_rgb_str(color_hex))
    etree.SubElement(srgbClr, _a("alpha"), val=str(alpha_pct * 1000))


def glow(shape, radius_pt: int = 8, color_hex: str = "#FFFFFF",
         alpha_pct: int = 50) -> None:
    """Add a glow effect to a shape."""
    sp = shape._element
    spPr = sp.find(_a("spPr"))
    if spPr is None:
        spPr = etree.SubElement(sp, _a("spPr"))

    effectLst = spPr.find(_a("effectLst"))
    if effectLst is None:
        effectLst = etree.SubElement(spPr, _a("effectLst"))

    existing = effectLst.find(_a("glow"))
    if existing is not None:
        effectLst.remove(existing)

    glowEl = etree.SubElement(effectLst, _a("glow"),
                               rad=str(Pt(radius_pt).emu))
    srgbClr = etree.SubElement(glowEl, _a("srgbClr"),
                                val=_hex_to_rgb_str(color_hex))
    etree.SubElement(srgbClr, _a("alpha"), val=str(alpha_pct * 1000))


def rounded_corners(shape, radius_pt: int = 6) -> None:
    """Apply rounded corners to a rectangle shape."""
    sp = shape._element
    spPr = sp.find(_a("spPr"))
    if spPr is None:
        spPr = etree.SubElement(sp, _a("spPr"))

    prstGeom = spPr.find(_a("prstGeom"))
    if prstGeom is not None:
        spPr.remove(prstGeom)

    prstGeom = etree.SubElement(spPr, _a("prstGeom"), prst="roundRect")
    avLst = etree.SubElement(prstGeom, _a("avLst"))
    # adj value: radius as percentage of min(w,h) * 100000
    radius_val = min(radius_pt * 1000, 50000)
    etree.SubElement(avLst, _a("gd"), name="adj", fmla=f"val {radius_val}")


def inner_border(shape, color_hex: str, width_pt: float = 1.0) -> None:
    """Add a solid border/line to a shape."""
    from pptx.util import Pt as PtUtil
    sp = shape._element
    spPr = sp.find(_a("spPr"))
    if spPr is None:
        spPr = etree.SubElement(sp, _a("spPr"))

    existing_ln = spPr.find(_a("ln"))
    if existing_ln is not None:
        spPr.remove(existing_ln)

    ln = etree.SubElement(spPr, _a("ln"), w=str(int(PtUtil(width_pt).emu / 12700)))
    solidFill = etree.SubElement(ln, _a("solidFill"))
    etree.SubElement(solidFill, _a("srgbClr"), val=_hex_to_rgb_str(color_hex))


def slide_gradient_background(slide, stops: list[tuple[int, str]],
                               angle_deg: int = 135) -> None:
    """Apply a gradient background to an entire slide via bg element."""
    spTree = slide.shapes._spTree
    # Find or create bg element in slide XML
    slide_el = slide._element
    cSld = slide_el.find(
        "{http://schemas.openxmlformats.org/presentationml/2006/main}cSld"
    )
    if cSld is None:
        return

    bg = cSld.find(
        "{http://schemas.openxmlformats.org/presentationml/2006/main}bg"
    )
    if bg is not None:
        cSld.remove(bg)

    p_ns = "http://schemas.openxmlformats.org/presentationml/2006/main"
    bg = etree.SubElement(cSld, f"{{{p_ns}}}bg")
    bgPr = etree.SubElement(bg, f"{{{p_ns}}}bgPr")

    gradFill = etree.SubElement(bgPr, _a("gradFill"))
    gsLst = etree.SubElement(gradFill, _a("gsLst"))

    for pos_pct, hex_color in stops:
        gs = etree.SubElement(gsLst, _a("gs"), pos=str(pos_pct * 1000))
        solidFill = etree.SubElement(gs, _a("solidFill"))
        etree.SubElement(solidFill, _a("srgbClr"), val=_hex_to_rgb_str(hex_color))

    etree.SubElement(gradFill, _a("lin"),
                     ang=str(int(angle_deg * 60000)),
                     scaled="0")
    etree.SubElement(bgPr, _a("effectLst"))
