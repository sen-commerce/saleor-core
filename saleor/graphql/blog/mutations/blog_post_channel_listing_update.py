import datetime
from collections import defaultdict
import graphene
from django.core.exceptions import ValidationError

from ....blog import models
from ....blog.error_codes import BlogErrorCode
from ....core.tracing import traced_atomic_transaction
from ...channel.mutations import BaseChannelListingMutation
from ...channel.types import Channel
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.scalars import DateTime
from ...core.types import BaseInputObjectType, NonNullList
from ..types import BlogPost, BlogError


class BlogPostChannelListingAddInput(BaseInputObjectType):
    channel_id = graphene.ID(required=True, description="ID of a channel.")
    is_published = graphene.Boolean(
        required=True, description="Determines if object is visible to customers in this channel."
    )
    published_at = DateTime(description="Publication date time. ISO 8601 standard.")


class BlogPostChannelListingUpdateInput(BaseInputObjectType):
    update_channels = NonNullList(
        BlogPostChannelListingAddInput,
        description="List of channels to which the blog post should be assigned or updated.",
        required=False,
    )
    remove_channels = NonNullList(
        graphene.ID,
        description="List of channels from which the blog post should be unassigned.",
        required=False,
    )


class BlogPostChannelListingUpdate(BaseChannelListingMutation):
    blog_post = graphene.Field(BlogPost, description="An updated blog post instance.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a blog post to update.")
        input = BlogPostChannelListingUpdateInput(
            required=True,
            description="Fields required to create or update blog post channel listings.",
        )

    class Meta:
        description = "Manage blog post's availability in channels."
        permissions = ()
        error_type_class = BlogError
        error_type_field = "blog_errors"

    @classmethod
    def clean_channels(cls, info: ResolveInfo, input, errors, error_code_enum_value, input_source="update_channels"):
        # We can inherit from BaseChannelListingMutation's clean_channels
        # and resolve Channel nodes.
        return super().clean_channels(info, input, errors, error_code_enum_value, input_source)

    @classmethod
    def update_channels(cls, blog_post: models.BlogPost, update_channels: list[dict]):
        for update_channel in update_channels:
            channel = update_channel["channel"]
            defaults = {}
            for field in ["is_published", "published_at"]:
                if field in update_channel.keys():
                    defaults[field] = update_channel[field]
            
            # If is_published is True and published_at is not set, set to now
            if defaults.get("is_published") and not defaults.get("published_at"):
                defaults["published_at"] = datetime.datetime.now(tz=datetime.UTC)

            models.BlogPostChannelListing.objects.update_or_create(
                blog_post=blog_post, channel=channel, defaults=defaults
            )

    @classmethod
    def remove_channels(cls, blog_post: models.BlogPost, remove_channels: list[int]):
        models.BlogPostChannelListing.objects.filter(
            blog_post=blog_post, channel_id__in=remove_channels
        ).delete()

    @classmethod
    def save(cls, info: ResolveInfo, blog_post: models.BlogPost, cleaned_input: dict):
        with traced_atomic_transaction():
            cls.update_channels(blog_post, cleaned_input.get("update_channels", []))
            cls.remove_channels(blog_post, cleaned_input.get("remove_channels", []))

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, id, input):
        blog_post = cls.get_node_or_error(info, id, only_type=BlogPost, field="id")
        errors = defaultdict(list)

        cleaned_input = cls.clean_channels(
            info,
            input,
            errors,
            BlogErrorCode.DUPLICATED_INPUT_ITEM.value,
            input_source="update_channels",
        )
        cls.clean_publication_date(
            errors, BlogErrorCode, cleaned_input, input_source="update_channels"
        )
        if errors:
            raise ValidationError(errors)

        cls.save(info, blog_post, cleaned_input)
        
        return BlogPostChannelListingUpdate(
            blog_post=ChannelContext(node=blog_post, channel_slug=None)
        )
