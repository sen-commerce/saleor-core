import graphene

from ....blog import models
from ...core.mutations import DeprecatedModelMutation
from ..types import BlogAuthor, BlogError


class BlogAuthorDelete(DeprecatedModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a blog author to delete.")

    class Meta:
        description = "Deletes a blog author."
        model = models.BlogAuthor
        object_type = BlogAuthor
        permissions = ()
        error_type_class = BlogError
        error_type_field = "blog_errors"
