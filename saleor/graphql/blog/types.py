import graphene

from ...blog import models
from ..core.context import ChannelContext
from ..core.connection import CountableConnection
from ..core.federation import federated_entity
from ..core.fields import JSONString
from ..core.scalars import DateTime
from ..core.types import Error, ModelObjectType
from ..core.types.context import ChannelContextType
from ..meta.types import ObjectWithMetadata


@federated_entity("id")
class BlogCategory(ModelObjectType[models.BlogCategory]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    slug = graphene.String(required=True)
    description = graphene.String()

    class Meta:
        description = "A blog category."
        interfaces = (graphene.relay.Node, ObjectWithMetadata)
        model = models.BlogCategory


class BlogCategoryCountableConnection(CountableConnection):
    class Meta:
        node = BlogCategory


@federated_entity("id")
class BlogAuthor(ModelObjectType[models.BlogAuthor]):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    slug = graphene.String(required=True)
    bio = graphene.String()
    avatar_url = graphene.String()

    class Meta:
        description = "A blog author profile."
        interfaces = (graphene.relay.Node,)
        model = models.BlogAuthor


class BlogAuthorCountableConnection(CountableConnection):
    class Meta:
        node = BlogAuthor


@federated_entity("id")
class BlogPost(ChannelContextType, ModelObjectType[models.BlogPost]):
    id = graphene.GlobalID(required=True)
    title = graphene.String(required=True)
    slug = graphene.String(required=True)
    content = JSONString(description="TipTap JSON content.")
    featured_comments = JSONString(description="Featured static comments.")
    featured_image = graphene.String()
    reading_time_minutes = graphene.Int()
    created_at = DateTime(required=True)
    updated_at = DateTime(required=True)

    is_published = graphene.Boolean()
    published_at = DateTime()
    translation = graphene.Field(
        "saleor.graphql.blog.types.BlogPostTranslation",
        language_code=graphene.Argument(
            graphene.String,
            required=True,
            description="A language code to return translation for.",
        ),
        description="Returns translation of a blog post for a given language.",
    )

    author = graphene.Field(BlogAuthor)
    category = graphene.Field(BlogCategory)

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = "A blog post."
        interfaces = (graphene.relay.Node, ObjectWithMetadata)
        model = models.BlogPost

    @staticmethod
    def resolve_author(root, _info):
        node = getattr(root, 'node', root)
        return node.author

    @staticmethod
    def resolve_category(root, _info):
        node = getattr(root, 'node', root)
        return node.category

    @staticmethod
    def resolve_is_published(root, _info):
        node = getattr(root, 'node', root)
        channel_slug = getattr(root, 'channel_slug', None)
        if channel_slug:
            listing = node.channel_listings.filter(channel__slug=channel_slug).first()
            if listing:
                return listing.is_published
        return node.is_published

    @staticmethod
    def resolve_published_at(root, _info):
        node = getattr(root, 'node', root)
        channel_slug = getattr(root, 'channel_slug', None)
        if channel_slug:
            listing = node.channel_listings.filter(channel__slug=channel_slug).first()
            if listing:
                return listing.published_at
        return node.published_at

    @staticmethod
    def resolve_translation(root, _info, language_code):
        node = getattr(root, 'node', root)
        return node.translations.filter(language_code=language_code).first()


class BlogPostTranslation(ModelObjectType[models.BlogPostTranslation]):
    id = graphene.GlobalID(required=True)
    title = graphene.String()
    content = JSONString(description="Translated TipTap JSON content.")

    class Meta:
        description = "A blog post translation."
        interfaces = (graphene.relay.Node,)
        model = models.BlogPostTranslation


class BlogPostCountableConnection(CountableConnection):
    class Meta:
        node = BlogPost


# Error types for Blog mutations
from ...blog.error_codes import BlogErrorCode as BlogErrorCodeEnum

BlogErrorCode = graphene.Enum.from_enum(BlogErrorCodeEnum)


class BlogError(Error):
    code = BlogErrorCode(description="The error code.", required=True)

    class Meta:
        description = "Represents an error in Blog mutation."

