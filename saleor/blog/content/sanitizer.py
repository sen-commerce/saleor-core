"""TipTap/ProseMirror JSON content sanitizer for Blog posts.

Independent from the EditorJS sanitizer — this module validates and cleans
TipTap JSON documents without touching any existing EditorJS code.

Security approach:
- Node type whitelist: only known node types are allowed
- Mark whitelist: only known formatting marks are allowed
- Text content: sanitized via nh3 (same library used by EditorJS cleaners)
- URLs: validated against a scheme whitelist (http, https only)
- Unknown fields: stripped during traversal
"""

import copy
import logging
from urllib.parse import urlparse

import nh3

logger = logging.getLogger(__name__)

# Allowed TipTap/ProseMirror node types
ALLOWED_NODE_TYPES = frozenset(
    {
        "doc",
        "paragraph",
        "heading",
        "text",
        "image",
        "bulletList",
        "orderedList",
        "listItem",
        "blockquote",
        "codeBlock",
        "horizontalRule",
        "table",
        "tableRow",
        "tableCell",
        "tableHeader",
        "hardBreak",
        "taskList",
        "taskItem",
    }
)

# Allowed TipTap mark types (inline formatting)
ALLOWED_MARKS = frozenset(
    {
        "bold",
        "italic",
        "underline",
        "strike",
        "code",
        "link",
        "highlight",
        "textStyle",
        "subscript",
        "superscript",
    }
)

# URL schemes allowed in links and images
ALLOWED_URL_SCHEMES = frozenset({"http", "https"})

# HTML tags allowed within text content (via nh3)
ALLOWED_HTML_TAGS = frozenset(
    {"b", "i", "em", "strong", "a", "br", "u", "s", "mark", "code", "span"}
)


def _clean_url(url: str | None) -> str | None:
    """Validate and clean a URL, allowing only http/https schemes."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ALLOWED_URL_SCHEMES:
            return None
        return url
    except Exception:
        return None


def _clean_text(text: str) -> str:
    """Sanitize text content using nh3."""
    return nh3.clean(text, tags=ALLOWED_HTML_TAGS)


def _clean_marks(marks: list[dict]) -> list[dict]:
    """Filter and clean marks (inline formatting)."""
    cleaned = []
    for mark in marks:
        mark_type = mark.get("type")
        if mark_type not in ALLOWED_MARKS:
            continue

        clean_mark: dict = {"type": mark_type}

        # Clean link marks — validate href
        if mark_type == "link" and "attrs" in mark:
            attrs = mark["attrs"]
            href = _clean_url(attrs.get("href"))
            if href:
                clean_mark["attrs"] = {
                    "href": href,
                    "target": attrs.get("target", "_blank"),
                    "rel": attrs.get("rel", "noopener noreferrer nofollow"),
                }
            else:
                continue  # Skip links with invalid URLs

        # Pass through simple attrs for other marks
        elif "attrs" in mark:
            clean_mark["attrs"] = mark["attrs"]

        cleaned.append(clean_mark)

    return cleaned


def _clean_node(node: dict, depth: int = 0) -> dict | None:
    """Recursively clean a TipTap document node.

    Returns None if the node should be removed.
    """
    if depth > 50:
        logger.warning("TipTap content exceeded maximum nesting depth")
        return None

    node_type = node.get("type", "")
    if node_type not in ALLOWED_NODE_TYPES:
        logger.info("Stripped unknown TipTap node type: %s", node_type)
        return None

    cleaned: dict = {"type": node_type}

    # Clean text content
    if "text" in node:
        cleaned["text"] = _clean_text(str(node["text"]))

    # Clean marks (formatting)
    if "marks" in node and isinstance(node["marks"], list):
        cleaned_marks = _clean_marks(node["marks"])
        if cleaned_marks:
            cleaned["marks"] = cleaned_marks

    # Clean attributes based on node type
    if "attrs" in node and isinstance(node["attrs"], dict):
        cleaned_attrs = _clean_attrs(node_type, node["attrs"])
        if cleaned_attrs:
            cleaned["attrs"] = cleaned_attrs

    # Recurse into children
    if "content" in node and isinstance(node["content"], list):
        cleaned_content = []
        for child in node["content"]:
            if isinstance(child, dict):
                cleaned_child = _clean_node(child, depth + 1)
                if cleaned_child is not None:
                    cleaned_content.append(cleaned_child)
        if cleaned_content:
            cleaned["content"] = cleaned_content

    return cleaned


def _clean_attrs(node_type: str, attrs: dict) -> dict:
    """Clean node attributes based on node type."""
    cleaned = {}

    if node_type == "heading":
        level = attrs.get("level", 2)
        if isinstance(level, int) and 1 <= level <= 6:
            cleaned["level"] = level
        else:
            cleaned["level"] = 2

    elif node_type == "image":
        src = _clean_url(attrs.get("src"))
        if src:
            cleaned["src"] = src
        alt = attrs.get("alt")
        if alt and isinstance(alt, str):
            cleaned["alt"] = _clean_text(alt)
        title = attrs.get("title")
        if title and isinstance(title, str):
            cleaned["title"] = _clean_text(title)

    elif node_type == "codeBlock":
        language = attrs.get("language")
        if language and isinstance(language, str):
            cleaned["language"] = language[:50]  # Limit length

    elif node_type in ("tableCell", "tableHeader"):
        for key in ("colspan", "rowspan"):
            val = attrs.get(key)
            if isinstance(val, int) and 1 <= val <= 10:
                cleaned[key] = val

    elif node_type == "taskItem":
        checked = attrs.get("checked")
        if isinstance(checked, bool):
            cleaned["checked"] = checked

    # textAlign for paragraphs/headings
    text_align = attrs.get("textAlign")
    if text_align in ("left", "center", "right", "justify"):
        cleaned["textAlign"] = text_align

    return cleaned


def clean_tiptap_content(data: dict | None) -> dict | None:
    """Validate and sanitize TipTap JSON content.

    This is the main entry point for cleaning blog post content.

    :param data: TipTap JSON document (or None)
    :returns: Cleaned copy of the document (or None)
    """
    if data is None:
        return None

    if not isinstance(data, dict):
        return None

    # Work on a deep copy to avoid mutating the input
    data = copy.deepcopy(data)

    # Ensure it's a doc node
    if data.get("type") != "doc":
        data = {"type": "doc", "content": [data]}

    return _clean_node(data)
