from django.db import models
from django.urls import reverse
from django.utils import timezone

from .utils import blog_upload_path, generate_unique_slug, sync_file_url


class PublishedPostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Post.Status.PUBLISHED)


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("vorin_blog:category_detail", kwargs={"slug": self.slug})


class Tag(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    excerpt = models.TextField(blank=True, help_text="Short summary shown in cards and listings.")
    content = models.TextField(blank=True, help_text="Legacy or rich HTML content for the post body.")
    featured_image = models.URLField(max_length=500, blank=True, verbose_name="Thumbnail image URL")
    featured_image_file = models.FileField(upload_to=blog_upload_path, blank=True, verbose_name="Thumbnail image file")
    featured_image_alt = models.CharField(max_length=255, blank=True, verbose_name="Thumbnail image alt text")
    header_image = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="Header image URL",
        help_text="Wide banner image shown at the top of the detail page.",
    )
    header_image_file = models.FileField(upload_to=blog_upload_path, blank=True, verbose_name="Header image file")
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="posts",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    is_featured = models.BooleanField(default=False)
    show_on_homepage = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    meta_title = models.CharField(max_length=70, blank=True, help_text="Optional SEO title override.")
    meta_description = models.CharField(max_length=160, blank=True, help_text="Optional SEO description override.")
    canonical_url = models.URLField(blank=True)
    original_url = models.CharField(max_length=500, blank=True, help_text="Legacy source URL for redirects or imports.")

    objects = PublishedPostQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.title)
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
        sync_file_url(self, "featured_image_file", "featured_image")
        sync_file_url(self, "header_image_file", "header_image")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("vorin_blog:post_detail", kwargs={"slug": self.slug})

    def get_header_image(self):
        return self.header_image or self.featured_image

    @property
    def effective_meta_title(self):
        return self.meta_title or self.title

    @property
    def effective_meta_description(self):
        return self.meta_description or self.excerpt


class PostImage(models.Model):
    post = models.ForeignKey(Post, related_name="images", on_delete=models.CASCADE)
    image_url = models.URLField(max_length=500, blank=True)
    image_file = models.FileField(upload_to=blog_upload_path, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    caption = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        sync_file_url(self, "image_file", "image_url")

    def __str__(self):
        return f"{self.post.title} - Image {self.order}"


class PostBlock(models.Model):
    class BlockType(models.TextChoices):
        INTRO = "intro", "Intro Paragraph"
        TEXT = "text", "Text Section"
        IMAGE = "image", "Single Image"
        IMAGE_PAIR = "image_pair", "Two Images Side by Side"
        QUOTE = "quote", "Pull Quote"

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="blocks")
    block_type = models.CharField(max_length=20, choices=BlockType.choices)
    order = models.PositiveIntegerField(default=0)
    heading = models.CharField(max_length=200, blank=True)
    body_text = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    image_file = models.FileField(upload_to=blog_upload_path, blank=True)
    image_alt = models.CharField(max_length=255, blank=True)
    image_caption = models.CharField(max_length=300, blank=True)
    image2_url = models.URLField(max_length=500, blank=True)
    image2_file = models.FileField(upload_to=blog_upload_path, blank=True)
    image2_alt = models.CharField(max_length=255, blank=True)
    quote_text = models.TextField(blank=True)
    quote_author = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["post", "order", "id"]
        verbose_name = "Story Section"
        verbose_name_plural = "Story Sections"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        sync_file_url(self, "image_file", "image_url")
        sync_file_url(self, "image2_file", "image2_url")

    def get_image_url(self):
        if self.image_file:
            try:
                return self.image_file.url
            except (ValueError, AttributeError):
                pass
        return self.image_url

    def get_image2_url(self):
        if self.image2_file:
            try:
                return self.image2_file.url
            except (ValueError, AttributeError):
                pass
        return self.image2_url

    def __str__(self):
        return f"{self.get_block_type_display()} #{self.order} - {self.post.title}"
