import graphene
from django.utils import timezone

from ...blog import models
from ...permission.enums import PagePermissions
from ..core.context import ChannelContext


def resolve_blog_post(info, id=None, slug=None, channel=None):
    user = info.context.user
    has_manage_permission = user and user.has_perm(PagePermissions.MANAGE_PAGES)

    if id:
        _type, pk = graphene.Node.from_global_id(id)
        post = models.BlogPost.objects.filter(pk=pk).first()
    elif slug:
        post = models.BlogPost.objects.filter(slug=slug).first()
    else:
        return None

    if post:
        if not has_manage_permission:
            # For public customers, check publication status
            if channel:
                listing = post.channel_listings.filter(
                    channel__slug=channel,
                    is_published=True,
                    published_at__lte=timezone.now()
                ).first()
                if not listing:
                    return None
            else:
                if not post.is_published or (post.published_at and post.published_at > timezone.now()):
                    return None
        return ChannelContext(node=post, channel_slug=channel)
    return None


def resolve_blog_posts(info, **kwargs):
    channel_slug = kwargs.get("channel")
    qs = models.BlogPost.objects.all()

    user = info.context.user
    has_manage_permission = user and user.has_perm(PagePermissions.MANAGE_PAGES)

    if not has_manage_permission:
        # For public customers, filter published articles only
        if channel_slug:
            listings = models.BlogPostChannelListing.objects.filter(
                channel__slug=channel_slug,
                is_published=True,
                published_at__lte=timezone.now()
            )
            qs = qs.filter(id__in=listings.values_list("blog_post_id", flat=True))
        else:
            qs = qs.filter(
                is_published=True,
                published_at__lte=timezone.now()
            )

    return qs

def resolve_blog_categories(info, **kwargs):
    return models.BlogCategory.objects.all()


def resolve_blog_authors(info, **kwargs):
    return models.BlogAuthor.objects.all()

