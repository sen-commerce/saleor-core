"""Blog error codes."""

from enum import Enum


class BlogErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    NOT_BLOG_POST_IMAGE = "not_blog_post_image"
    INVALID_CONTENT = "invalid_content"
