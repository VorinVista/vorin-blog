import re

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None


EMPTY_TEXT_RE = re.compile(r"^[\s\xa0\u200b\u200c\u200d\ufeff|\-]*$")


def _normalize_text(value):
    return re.sub(r"\s+", " ", (value or "")).strip()


def _pick_best_image_src(candidates):
    best_src = None
    best_score = -1

    for src in candidates:
        value = (src or "").strip()
        if not value:
            continue

        score = 0
        if value.startswith(("https://", "http://")):
            score += 5
        if "wp-content/uploads/" in value:
            score += 4
        if re.search(r"\.(jpe?g|png|webp|gif)(?:\?|$)", value, flags=re.IGNORECASE):
            score += 2
        if "/" in value:
            score += 1

        if score > best_score:
            best_score = score
            best_src = value

    return best_src


def _pick_best_alt_text(candidates):
    best_alt = ""
    best_score = -1

    for alt in candidates:
        value = _normalize_text(alt)
        if not value:
            continue

        score = len(value)
        if " " in value:
            score += 20
        if re.search(r"[A-Z]", value):
            score += 5
        if "-" in value and " " not in value:
            score -= 10

        if score > best_score:
            best_score = score
            best_alt = value

    return best_alt


def _extract_best_image_data(fragment):
    src_candidates = re.findall(r'src="([^"]+)"', fragment, flags=re.IGNORECASE)
    alt_candidates = re.findall(r'alt="([^"]*)"', fragment, flags=re.IGNORECASE)
    src = _pick_best_image_src(src_candidates)
    alt = _pick_best_alt_text(alt_candidates)
    if not src:
        return None
    return {"src": src, "alt": alt}


def _is_heading_candidate(text):
    normalized = _normalize_text(text)
    if not normalized:
        return False
    if re.fullmatch(r"https?://\S+", normalized, flags=re.IGNORECASE):
        return False
    if len(normalized) > 90:
        return False
    if len(normalized.split()) > 14:
        return False
    if "," in normalized or ";" in normalized:
        return False
    if normalized.endswith((".", "!")):
        return False
    if normalized.lower().startswith("tip:"):
        return False
    return True


def _cleanup_editorial_structure(soup):
    previous_text = None

    for heading in list(soup.find_all(["h2", "h3", "h4"])):
        heading_text = _normalize_text(heading.get_text(" ", strip=True))
        if re.fullmatch(r"https?://\S+", heading_text, flags=re.IGNORECASE):
            heading.decompose()

    for paragraph in list(soup.find_all("p")):
        if paragraph.find(["img", "iframe", "video"]):
            previous_text = None
            continue

        text = _normalize_text(paragraph.get_text(" ", strip=True))
        if not text or EMPTY_TEXT_RE.match(text):
            paragraph.decompose()
            continue

        if re.fullmatch(r"https?://\S+", text, flags=re.IGNORECASE):
            paragraph.decompose()
            continue

        if previous_text == text:
            paragraph.decompose()
            continue

        next_tag = paragraph.find_next_sibling()
        if _is_heading_candidate(text):
            if text.endswith(":") and next_tag and next_tag.name in {"ul", "ol"}:
                paragraph.name = "h3"
            elif not re.search(r"[.!]$", text):
                paragraph.name = "h2"

        previous_text = text if paragraph.name == "p" else None


def normalize_post_content(raw_content):
    if not raw_content:
        return ""

    content = raw_content
    content = re.sub(r"<!--\s*wp:.*?-->", "", content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r"<!--\s*/wp:.*?-->", "", content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r"\[(?:/?vc_[^\]]+|/?et_pb[^\]]+|/?gallery[^\]]*)\]", "", content, flags=re.IGNORECASE)

    if BeautifulSoup is None:
        content = re.sub(r"^\s*<h1[^>]*>.*?</h1>\s*", "", content, count=1, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r"<p>\s*(?:&nbsp;|\s|<br\s*/?>)*</p>", "", content, flags=re.IGNORECASE)
        return content.strip()

    soup = BeautifulSoup(content, "html.parser")

    for tag in soup.find_all(True):
        for attr in ["style", "width", "height", "srcset", "sizes", "decoding", "fetchpriority"]:
            tag.attrs.pop(attr, None)

    first_h1 = soup.find("h1")
    if first_h1:
        first_h1.decompose()

    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            img.decompose()
            continue

        cleaned_attrs = {"src": src, "loading": "lazy", "class": "rb-post-body-image"}
        alt_text = img.get("alt")
        if alt_text:
            cleaned_attrs["alt"] = alt_text
        img.attrs = cleaned_attrs

    for anchor in soup.find_all("a"):
        href = anchor.get("href", "").strip()
        if href in {"https://example.com", "http://example.com", "your-link-here.html"}:
            anchor.unwrap()

    for figure in soup.find_all("figure"):
        figure_fragment = str(figure)
        recovered_data = _extract_best_image_data(figure_fragment)
        existing_img = figure.find("img")

        if recovered_data and not existing_img:
            recovered_img = soup.new_tag("img")
            recovered_img["src"] = recovered_data["src"]
            recovered_img["loading"] = "lazy"
            recovered_img["class"] = "rb-post-body-image"
            if recovered_data["alt"]:
                recovered_img["alt"] = recovered_data["alt"]
            figure.clear()
            figure.attrs = {}
            figure.append(recovered_img)

        if not figure.find("img") and not figure.get_text(strip=True):
            figure.decompose()

    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(strip=True)
        if not text and not paragraph.find("img"):
            paragraph.decompose()

    _cleanup_editorial_structure(soup)

    return str(soup).strip()


def detect_post_content_issues(raw_content):
    content = raw_content or ""
    duplicate_paragraph = re.search(
        r"<p>\s*([^<][^<]{1,120}?)\s*</p>\s*<p>\s*\1\s*</p>",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    ) is not None
    spacer_paragraph = re.search(r"<p>\s*(?:&nbsp;|\s|\|)+\s*</p>", content, flags=re.IGNORECASE) is not None
    checks = {
        "placeholder_link": re.search(r"your-link-here\.html|example\.com", content, flags=re.IGNORECASE) is not None,
        "duplicate_paragraph": duplicate_paragraph,
        "spacer_paragraph": spacer_paragraph,
    }
    return {name: value for name, value in checks.items() if value}

