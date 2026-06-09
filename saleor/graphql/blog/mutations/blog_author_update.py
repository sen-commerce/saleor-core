import graphene

from ....blog import models
from ...core.mutations import DeprecatedModelMutation
from ..types import BlogAuthor, BlogError
from .blog_author_create import BlogAuthorInput


class BlogAuthorUpdate(DeprecatedModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a blog author to update.")
        input = BlogAuthorInput(
            required=True, description="Fields required to update a blog author."
        )

    class Meta:
        description = "Updates an existing blog author."
        model = models.BlogAuthor
        object_type = BlogAuthor
        permissions = ()
        error_type_class = BlogError
        error_type_field = "blog_errors"
