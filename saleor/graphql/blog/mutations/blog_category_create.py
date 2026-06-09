import graphene
from django.core.exceptions import ValidationError

from ....blog import models
from ....blog.error_codes import BlogErrorCode
from ...core import ResolveInfo
from ...core.mutations import DeprecatedModelMutation
from ...core.types import BaseInputObjectType
from ...core.validators import validate_slug_and_generate_if_needed
from ..types import BlogCategory, BlogError


class BlogCategoryInput(BaseInputObjectType):
    name = graphene.String(description="Category name.")
    slug = graphene.String(description="Category slug.")
    description = graphene.String(description="Category description.")
    parent = graphene.ID(description="ID of the parent category.", required=False)


class BlogCategoryCreate(DeprecatedModelMutation):
    class Arguments:
        input = BlogCategoryInput(
            required=True, description="Fields required to create a blog category."
        )

    class Meta:
        description = "Creates a new blog category."
        model = models.BlogCategory
        object_type = BlogCategory
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
