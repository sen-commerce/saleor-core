import graphene

from ....blog import models
from ...core.context import ChannelContext
from ...core.mutations import DeprecatedModelMutation
from ..types import BlogPost, BlogError
from .blog_post_create import BlogPostCreate, BlogPostInput


class BlogPostUpdate(BlogPostCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a blog post to update.")
        input = BlogPostInput(
            required=True, description="Fields required to update a blog post."
        )

    class Meta:
        description = "Updates an existing blog post."
        model = models.BlogPost
        object_type = BlogPost
        permissions = ()
        error_type_class = BlogError
        error_type_field = "blog_errors"

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.blog_post = ChannelContext(instance, channel_slug=None)
        return response
