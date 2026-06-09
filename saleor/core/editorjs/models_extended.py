"""Extended EditorJS block models for additional block types.

These models extend the base EditorJS support with additional block types:
delimiter, code, table, warning, checklist, and raw HTML.

All models follow the same security patterns as the core models:
- StrictBaseModel with extra="ignore" to drop unknown fields
- Text type with nh3 HTML sanitization via _clean_text
- URL type with scheme whitelist validation via _clean_url_value
"""

from typing import Literal

from pydantic import Field

from .models import EditorJSBlock, StrictBaseModel, Text


# ── Delimiter ────────────────────────────────────────────────────────────────


class EditorJSDelimiterDataModel(StrictBaseModel):
    """Empty data model for delimiter (horizontal rule)."""

    pass


class EditorJSDelimiterBlockModel(EditorJSBlock):
    """Match an EditorJS delimiter block object.

    Example:
        {
            "type": "delimiter",
            "data": {}
        }

    """

    type: Literal["delimiter"]
    data: EditorJSDelimiterDataModel = Field(
        default_factory=EditorJSDelimiterDataModel
    )
    id: Text | None = None

    def to_text(self) -> str:
        return "---"


# ── Code ─────────────────────────────────────────────────────────────────────


class EditorJSCodeDataModel(StrictBaseModel):
    """Match the data payload for an EditorJS code block.

    Example:
        {
            "code": "console.log('Hello');"
        }

    """

    code: Text | None = None


class EditorJSCodeBlockModel(EditorJSBlock):
    """Match an EditorJS code block object.

    Example:
        {
            "type": "code",
            "data": {
                "code": "console.log('Hello');"
            }
        }

    """

    type: Literal["code"]
    data: EditorJSCodeDataModel
    id: Text | None = None

    def to_text(self) -> str:
        return self.data.code or ""


# ── Table ────────────────────────────────────────────────────────────────────


class EditorJSTableDataModel(StrictBaseModel):
    """Match the data payload for an EditorJS table block.

    Example:
        {
            "withHeadings": true,
            "content": [
                ["Name", "Price"],
                ["Item 1", "$10"]
            ]
        }

    """

    withHeadings: bool | None = None
    content: list[list[Text | None]] | None = None


class EditorJSTableBlockModel(EditorJSBlock):
    """Match an EditorJS table block object.

    Example:
        {
            "type": "table",
            "data": {
                "withHeadings": true,
                "content": [
                    ["Name", "Price"],
                    ["Item 1", "$10"]
                ]
            }
        }

    """

    type: Literal["table"]
    data: EditorJSTableDataModel
    id: Text | None = None

    def to_text(self) -> str:
        if not self.data.content:
            return ""
        return " ".join(
            cell for row in self.data.content for cell in row if cell
        )


# ── Warning ──────────────────────────────────────────────────────────────────


class EditorJSWarningDataModel(StrictBaseModel):
    """Match the data payload for an EditorJS warning block.

    Example:
        {
            "title": "Note",
            "message": "This is important."
        }

    """

    title: Text | None = None
    message: Text | None = None


class EditorJSWarningBlockModel(EditorJSBlock):
    """Match an EditorJS warning block object.

    Example:
        {
            "type": "warning",
            "data": {
                "title": "Note",
                "message": "This is important."
            }
        }

    """

    type: Literal["warning"]
    data: EditorJSWarningDataModel
    id: Text | None = None

    def to_text(self) -> str:
        return " ".join(
            p for p in (self.data.title, self.data.message) if p
        )


# ── Checklist ────────────────────────────────────────────────────────────────


class EditorJSChecklistItemModel(StrictBaseModel):
    """Match a single checklist item.

    Example:
        {
            "text": "Buy groceries",
            "checked": true
        }

    """

    text: Text | None = None
    checked: bool | None = None


class EditorJSChecklistDataModel(StrictBaseModel):
    """Match the data payload for an EditorJS checklist block.

    Example:
        {
            "items": [
                {"text": "Buy groceries", "checked": true},
                {"text": "Clean house", "checked": false}
            ]
        }

    """

    items: list[EditorJSChecklistItemModel] | None = None


class EditorJSChecklistBlockModel(EditorJSBlock):
    """Match an EditorJS checklist block object.

    Example:
        {
            "type": "checklist",
            "data": {
                "items": [
                    {"text": "Buy groceries", "checked": true},
                    {"text": "Clean house", "checked": false}
                ]
            }
        }

    """

    type: Literal["checklist"]
    data: EditorJSChecklistDataModel
    id: Text | None = None

    def to_text(self) -> str:
        if not self.data.items:
            return ""
        return " ".join(
            item.text for item in self.data.items if item.text
        )


# ── Raw HTML ─────────────────────────────────────────────────────────────────


class EditorJSRawDataModel(StrictBaseModel):
    """Match the data payload for an EditorJS raw HTML block.

    Example:
        {
            "html": "<div class='custom'>Content</div>"
        }

    """

    html: Text | None = None


class EditorJSRawBlockModel(EditorJSBlock):
    """Match an EditorJS raw HTML block object.

    The HTML content is sanitized through the ``Text`` type validator
    which uses nh3 to strip disallowed tags and attributes.

    Example:
        {
            "type": "raw",
            "data": {
                "html": "<div class='custom'>Content</div>"
            }
        }

    """

    type: Literal["raw"]
    data: EditorJSRawDataModel
    id: Text | None = None

    def to_text(self) -> str:
        return self.data.html or ""
