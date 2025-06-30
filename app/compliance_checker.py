
def check_compliance(image_data, brandkit_data):
    score = 0
    reasoning = {}

    # 1. Font style
    if image_data.get("font_style_ok"):
        score += 1
        reasoning["font"] = "Font matches brand kit."
    else:
        reasoning["font"] = "Font does not match brand kit."

    # 2. Logo safe zone
    if image_data.get("logo_safe_zone_ok"):
        score += 1
        reasoning["safe_zone"] = "Logo respect safe zone."
    else:
        reasoning["safe_zone"] = "Logo violates safe zone."

    # 3. Logo colors
    if image_data.get("logo_colors_ok"):
        score += 1
        reasoning["logo_colors"] = "Logo colors match brand kit."
    else:
        reasoning["logo_colors"] = "Logo colors do not match."

    # 4. Color palette
    if image_data.get("palette_ok"):
        score += 1
        reasoning["palette"] = "Image color palette complies."
    else:
        reasoning["palette"] = "Image color palette does not comply."

    return score, reasoning