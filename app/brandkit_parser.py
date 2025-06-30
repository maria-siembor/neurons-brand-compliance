import fitz    
import re

def extract_brandkit_info(pdf_bytes):
    """
    Parses the Neurons brandkit PDF and extracts:
      - primary_font (e.g. "Lexend")
      - secondary_font (e.g. "Inter")
      - safe_zone_px (e.g. 30)
      - logo_colors (list of 5 hex strings)
      - primary_colors (same list for now)

    Raises ValueError if any required field is missing or cannot be parsed.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # 1. Extract fonts - scan all pages
    primary_font = None
    secondary_font = None

    for page in doc:
        lines = [ln.strip() for ln in page.get_text("text").splitlines()]
        for i, ln in enumerate(lines):
            if ln == "Primary":
                for j in range(i + 1, len(lines)):
                    candidate = lines[j].strip()
                    if candidate:
                        primary_font = candidate
                        break
            elif ln == "Secondary":
                for j in range(i + 1, len(lines)):
                    candidate = lines[j].strip()
                    if candidate:
                        secondary_font = candidate
                        break
        if primary_font and secondary_font:
            break

    if not primary_font or not secondary_font:
        raise ValueError(
            "Could not parse fonts from the brandkit PDF. "
        )

    # 2. Extract Safe Zone
    safe_zone_px = None
    px_pattern = re.compile(r"(\d+)\s*px", re.IGNORECASE)

    for page in doc:
        page_text = page.get_text("text")
        lower = page_text.lower()
        if "zone" in lower:
            match = px_pattern.search(page_text)
            if match:
                try:
                    safe_zone_px = int(match.group(1))
                except ValueError:
                    continue
                break

    if safe_zone_px is None:
        raise ValueError(
            "Could not parse Safe Zone from the brandkit PDF. "
        )
    

    # 3. Extract all distinct hex codes across pages
    hex_pattern = re.compile(r"#([0-9A-Fa-f]{6})")
    found_hexes = []

    for page in doc:
        page_text = page.get_text("text")
        for h in hex_pattern.findall(page_text):
            hx = "#" + h.upper()
            if hx not in found_hexes:
                found_hexes.append(hx)
        if len(found_hexes) >= 5:
            break

    if len(found_hexes) < 5:
        raise ValueError(
            f"Expected at least 5 distinct hex codes for logo colors, but found {len(found_hexes)}."
        )

    logo_colors = found_hexes[:5]
    primary_colors = logo_colors.copy()

    return {
        "primary_font": primary_font,
        "secondary_font": secondary_font,
        "safe_zone_px": safe_zone_px,
        "logo_colors": logo_colors,
        "primary_colors": primary_colors
    }