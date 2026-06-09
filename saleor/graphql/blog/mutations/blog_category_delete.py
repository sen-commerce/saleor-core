import graphene

from ....blog import models
from ...core.mutations import DeprecatedModelMutation
from ..types import BlogCategory, BlogError


class BlogCategoryDelete(DeprecatedModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a blog category to delete.")

    class Meta:
        description = "Deletes a blog category."
        model = models.BlogCategory
        object_type = BlogCategory
        permissions = ()
        error_type_class = BlogError
        error_type_field = "blog_errors"
