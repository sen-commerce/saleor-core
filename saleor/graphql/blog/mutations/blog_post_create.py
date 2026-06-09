import datetime
import graphene
from django.core.exceptions import ValidationError

from ....blog import models
from ....blog.content.sanitizer import clean_tiptap_content
from ....blog.error_codes import BlogErrorCode
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.fields import JSONString
from ...core.mutations import DeprecatedModelMutation
from ...core.scalars import DateTime
from ...core.types import BaseInputObjectType, NonNullList
from ...core.validators import validate_slug_and_generate_if_needed
from ..types import BlogPost, BlogError


class BlogPostInput(BaseInputObjectType):
    title = graphene.String(description="Blog post title.")
    slug = graphene.String(description="Blog post slug.")
    content = JSONString(description="TipTap JSON content.")
    featured_comments = JSONString(description="Featured static comments JSON array.")
    author = graphene.ID(description="ID of the author.")
    category = graphene.ID(description="ID of the category.")
    featured_image = graphene.String(description="Featured image URL.")
    reading_time_minutes = graphene.Int(description="Estimated reading time in minutes.")
    is_published = graphene.Boolean(description="Determines if blog post is published.")
    published_at = DateTime(description="Publication date time.")
    tags = NonNullList(graphene.ID, description="List of blog tag IDs.")


class BlogPostCreate(DeprecatedModelMutation):
    class Arguments:
        input = BlogPostInput(
            required=True, description="Fields required to create a blog post."
        )

    class Meta:
        description = "Creates a new blog post."
        model = models.BlogPost
        object_type = BlogPost
        permissions = ()
        error_type_class = BlogError
        error_type_field = "blog_errors"

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "title", cleaned_input
            )
        except ValidationError as e:
            e.code = BlogErrorCode.REQUIRED.value
            raise ValidationError({"slug": e}) from e

        # Clean content
        content = cleaned_input.get("content")
        if content is not None:
            cleaned_input["content"] = clean_tiptap_content(content)

        # Validate featured comments JSON structure
        featured_comments = cleaned_input.get("featured_comments")
        if featured_comments is not None:
            if not isinstance(featured_comments, list):
                raise ValidationError(
                    {
                        "featured_comments": ValidationError(
                            "Featured comments must be a JSON array.",
                            code=BlogErrorCode.INVALID.value,
                        )
                    }
                )
            for comment in featured_comments:
                if not isinstance(comment, dict) or "author" not in comment or "text" not in comment:
                    raise ValidationError(
                        {
                            "featured_comments": ValidationError(
                                "Each comment must contain 'author' and 'text'.",
                                code=BlogErrorCode.INVALID.value,
                            )
                        }
                    )

        # Handle publication date
        is_published = cleaned_input.get("is_published")
        published_at = cleaned_input.get("published_at")
        if is_published and not published_at:
            cleaned_input["published_at"] = datetime.datetime.now(tz=datetime.UTC)
        elif "published_at" in cleaned_input:
            cleaned_input["published_at"] = published_at

        return cleaned_input

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        super().post_save_action(info, instance, cleaned_input)
        
        # Auto-sync the global publish status to all active channels
        from ....channel.models import Channel
        
        channels = Channel.objects.all()
        for channel in channels:
            models.BlogPostChannelListing.objects.update_or_create(
                blog_post=instance,
                channel=channel,
                defaults={
                    "is_published": instance.is_published,
                    "published_at": instance.published_at,
                }
            )

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.blog_post = ChannelContext(instance, channel_slug=None)
        return response
