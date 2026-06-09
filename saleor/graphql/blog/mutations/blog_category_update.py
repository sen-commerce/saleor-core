import graphene

from ....blog import models
from ...core.mutations import DeprecatedModelMutation
from ..types import BlogCategory, BlogError
from .blog_category_create import BlogCategoryInput


class BlogCategoryUpdate(DeprecatedModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a blog category to update.")
        input = BlogCategoryInput(
            required=True, description="Fields required to update a blog category."
        )

    class Meta:
        description = "Updates an existing blog category."
        model = models.BlogCategory
        object_type = BlogCategory
        permissions = ()
        error_type_class = BlogError
        error_type_field = "blog_errors"
