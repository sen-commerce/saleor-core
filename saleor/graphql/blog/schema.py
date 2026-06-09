import graphene

from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.context import ChannelQsContext
from ..core.fields import FilterConnectionField
from . import resolvers
from .mutations import (
    BlogAuthorCreate,
    BlogAuthorDelete,
    BlogAuthorUpdate,
    BlogCategoryCreate,
    BlogCategoryDelete,
    BlogCategoryUpdate,
    BlogPostChannelListingUpdate,
    BlogPostCreate,
    BlogPostDelete,
    BlogPostUpdate,
)
from .types import (
    BlogAuthor,
    BlogAuthorCountableConnection,
    BlogCategory,
    BlogCategoryCountableConnection,
    BlogPost,
    BlogPostCountableConnection,
)


class BlogQueries(graphene.ObjectType):
    blog_post = graphene.Field(
        BlogPost,
        id=graphene.Argument(graphene.ID),
        slug=graphene.Argument(graphene.String),
        channel=graphene.Argument(graphene.String),
        description="Look up a blog post by ID or slug.",
    )
    blog_posts = FilterConnectionField(
        BlogPostCountableConnection,
        channel=graphene.String(description="Slug of a channel."),
        description="List of blog posts.",
    )
    blog_categories = FilterConnectionField(
        BlogCategoryCountableConnection,
        description="List of blog categories.",
    )
    blog_authors = FilterConnectionField(
        BlogAuthorCountableConnection,
        description="List of blog authors.",
    )

    @staticmethod
    def resolve_blog_post(_root, info, **data):
        return resolvers.resolve_blog_post(info, **data)

    @staticmethod
    def resolve_blog_posts(_root, info, **kwargs):
        qs = resolvers.resolve_blog_posts(info, **kwargs)
        qs = ChannelQsContext(qs=qs, channel_slug=kwargs.get("channel"))
        return create_connection_slice(qs, info, kwargs, BlogPostCountableConnection)

    @staticmethod
    def resolve_blog_categories(_root, info, **kwargs):
        qs = resolvers.resolve_blog_categories(info, **kwargs)
        return create_connection_slice(qs, info, kwargs, BlogCategoryCountableConnection)

    @staticmethod
    def resolve_blog_authors(_root, info, **kwargs):
        qs = resolvers.resolve_blog_authors(info, **kwargs)
        return create_connection_slice(qs, info, kwargs, BlogAuthorCountableConnection)


class BlogMutations(graphene.ObjectType):
    blog_post_create = BlogPostCreate.Field()
    blog_post_update = BlogPostUpdate.Field()
    blog_post_delete = BlogPostDelete.Field()
    blog_post_channel_listing_update = BlogPostChannelListingUpdate.Field()

    blog_category_create = BlogCategoryCreate.Field()
    blog_category_update = BlogCategoryUpdate.Field()
    blog_category_delete = BlogCategoryDelete.Field()

    blog_author_create = BlogAuthorCreate.Field()
    blog_author_update = BlogAuthorUpdate.Field()
    blog_author_delete = BlogAuthorDelete.Field()

