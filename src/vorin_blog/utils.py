import os
import uuid

from django.utils.text import slugify


def blog_upload_path(instance, filename):
    extension = os.path.splitext(filename)[1].lower() or ".jpg"
    model_name = instance._meta.model_name
    return f"uploads/vorin_blog/{model_name}/{uuid.uuid4().hex}{extension}"


def sync_file_url(instance, file_field_name, url_field_name):
    file_field = getattr(instance, file_field_name, None)
    if not file_field:
        return

    try:
        local_url = file_field.url
    except (ValueError, AttributeError):
        return

    if getattr(instance, url_field_name, "") == local_url:
        return

    setattr(instance, url_field_name, local_url)
    if instance.pk:
        type(instance).objects.filter(pk=instance.pk).update(**{url_field_name: local_url})


def generate_unique_slug(instance, source_value, slug_field_name="slug"):
    slug_field = instance._meta.get_field(slug_field_name)
    max_length = slug_field.max_length
    base_slug = slugify(source_value)[:max_length].strip("-") or "item"
    slug = base_slug
    suffix = 1
    queryset = type(instance).objects.all()

    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    while queryset.filter(**{slug_field_name: slug}).exists():
        suffix_str = f"-{suffix}"
        slug = f"{base_slug[: max_length - len(suffix_str)].rstrip('-')}{suffix_str}"
        suffix += 1

    return slug
