"""Blog models for Saleor.

This module defines the data models for the Blog feature, including:
- BlogPost: The main blog article model with TipTap JSON content
- BlogCategory: Hierarchical blog categories
- BlogTag: Tags for blog posts
- BlogAuthor: Author profiles
- BlogPostChannelListing: Multi-channel publishing control
- BlogPostTranslation: Multi-language support

All models follow Saleor's established patterns:
- ModelWithMetadata for metadata support
- SeoModel for SEO fields
- PublishableModel for publish/draft state
- Channel-based visibility via ChannelListing
- Translation support via SeoModelTranslationWithSlug
"""

from django.db import models

from ..channel.models import Channel
from ..core.models import ModelWithMetadata, PublishableModel
from ..core.utils.translations import Translation
from ..seo.models import SeoModel, SeoModelTranslation


class BlogAuthor(models.Model):
    """Author profile for blog posts."""

    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True)
    bio = models.TextField(blank=True, default="")
    avatar_url = models.URLField(max_length=512, blank=True, default="")

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class BlogCategory(ModelWithMetadata):
    """Blog category with optional parent for hierarchy."""

    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
    )

    class Meta(ModelWithMetadata.Meta):
        ordering = ("name",)
        verbose_name_plural = "blog categories"

    def __str__(self):
        return self.name


class BlogTag(models.Model):
    """Tag for blog posts."""

    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=128, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class BlogPost(ModelWithMetadata, SeoModel, PublishableModel):
    """Main blog post model.

    Content is stored as TipTap JSON (independent from the EditorJS
    content used in Page/Product/Category models).

    Featured comments are stored as structured JSON data, not as a
    separate model, per the user's requirement for static comments.
    """

    slug = models.SlugField(max_length=255, unique=True)
    title = models.CharField(max_length=250)

    # TipTap JSON content — independent from EditorJS
    content = models.JSONField(blank=True, null=True)

    # Structured static comments: [{author, text, rating, avatar_url, ...}]
    featured_comments = models.JSONField(
        blank=True,
        null=True,
        help_text="Structured list of curated/static comments.",
    )

    # Relationships
    author = models.ForeignKey(
        BlogAuthor,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="posts",
    )
    category = models.ForeignKey(
        BlogCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="posts",
    )
    tags = models.ManyToManyField(BlogTag, blank=True, related_name="posts")

    # Media
    featured_image = models.URLField(max_length=512, blank=True, default="")

    # Computed / cached fields
    reading_time_minutes = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(ModelWithMetadata.Meta):
        ordering = ("-created_at",)

    def __str__(self):
        return self.title


class BlogPostChannelListing(models.Model):
    """Controls which channels a blog post is visible in.

    Each blog post can be independently published/unpublished
    per channel, following Saleor's multi-channel pattern.
    """

    blog_post = models.ForeignKey(
        BlogPost,
        related_name="channel_listings",
        on_delete=models.CASCADE,
    )
    channel = models.ForeignKey(
        Channel,
        related_name="blog_post_listings",
        on_delete=models.CASCADE,
    )
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (("blog_post", "channel"),)
        ordering = ("pk",)

    def __str__(self):
        return f"{self.blog_post.title} - {self.channel.slug}"


class BlogPostTranslation(SeoModelTranslation):
    """Translation for blog post content.

    Follows Saleor's translation pattern, storing translated
    title and TipTap JSON content per language.
    """

    blog_post = models.ForeignKey(
        BlogPost,
        related_name="translations",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    content = models.JSONField(blank=True, null=True)

    class Meta:
        unique_together = (("language_code", "blog_post"),)

    def get_translated_object_id(self):
        return "BlogPost", self.blog_post_id

    def get_translated_keys(self):
        translated_keys = super().get_translated_keys()
        translated_keys.update(
            {
                "title": self.title,
                "content": self.content,
            }
        )
        return translated_keys
