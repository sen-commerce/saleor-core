import graphene
from django.core.exceptions import ValidationError

from ....blog import models
from ....blog.error_codes import BlogErrorCode
from ...core import ResolveInfo
from ...core.mutations import DeprecatedModelMutation
from ...core.types import BaseInputObjectType
from ...core.validators import validate_slug_and_generate_if_needed
from ..types import BlogAuthor, BlogError


class BlogAuthorInput(BaseInputObjectType):
    name = graphene.String(description="Author name.")
    slug = graphene.String(description="Author slug.")
    bio = graphene.String(description="Author biography.")
    avatar_url = graphene.String(description="Author avatar URL.")


class BlogAuthorCreate(DeprecatedModelMutation):
    class Arguments:
        input = BlogAuthorInput(
            required=True, description="Fields required to create a blog author."
        )

    class Meta:
        description = "Creates a new blog author."
        model = models.BlogAuthor
        object_type = BlogAuthor
        # We can use standard page permission or general manage pages permissions
        permissions = ()
        error_type_class = BlogError
        error_type_field = "blog_errors"

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as e:
            e.code = BlogErrorCode.REQUIRED.value
            raise ValidationError({"slug": e}) from e

        return cleaned_input
