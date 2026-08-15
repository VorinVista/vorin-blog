from django import forms
from django.contrib import admin
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html

from .models import Category, Post, PostBlock, PostImage, Tag


def _build_content_widget(upload_url=None):
    try:
        from tinymce.widgets import TinyMCE
    except Exception:
        return forms.Textarea(attrs={"rows": 18})

    return TinyMCE(
        attrs={"cols": 120, "rows": 30},
        mce_attrs={
            "height": 700,
            "menubar": True,
            "branding": False,
            "toolbar_sticky": True,
            "automatic_uploads": True,
            "images_upload_url": upload_url or "/blog/admin/tinymce-image-upload/",
            "images_reuse_filename": True,
            "file_picker_types": "image",
            "paste_data_images": True,
        },
    )


def _format_datetime(value):
    if not value:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 0
    fields = ("order", "image_file", "image_url", "alt_text", "caption")
    ordering = ("order", "id")


class PostBlockInline(admin.StackedInline):
    model = PostBlock
    extra = 0
    ordering = ("order", "id")
    fields = [
        ("block_type", "order"),
        "heading",
        "body_text",
        "current_image_display",
        ("image_file", "image_url"),
        "image_alt",
        "image_caption",
        "current_image2_display",
        ("image2_file", "image2_url"),
        "image2_alt",
        "quote_text",
        "quote_author",
        "block_preview",
    ]
    readonly_fields = ["current_image_display", "current_image2_display", "block_preview"]

    def current_image_display(self, obj):
        image_url = obj.get_image_url() if obj.pk else ""
        if not image_url:
            return format_html("<span style='color:#777;'>No first image saved yet.</span>")
        return format_html(
            "<img src='{}' style='max-width:220px;max-height:160px;object-fit:contain;border-radius:8px;' alt='preview'>",
            image_url,
        )

    current_image_display.short_description = "Current first image"

    def current_image2_display(self, obj):
        image_url = obj.get_image2_url() if obj.pk else ""
        if not image_url:
            return format_html("<span style='color:#777;'>No second image saved yet.</span>")
        return format_html(
            "<img src='{}' style='max-width:220px;max-height:160px;object-fit:contain;border-radius:8px;' alt='preview'>",
            image_url,
        )

    current_image2_display.short_description = "Current second image"

    def block_preview(self, obj):
        if not obj.pk:
            return "-"
        if obj.block_type in {PostBlock.BlockType.INTRO, PostBlock.BlockType.TEXT}:
            preview = (obj.body_text or "")[:120]
            return preview or "-"
        if obj.block_type == PostBlock.BlockType.QUOTE:
            preview = (obj.quote_text or "")[:120]
            return preview or "-"
        if obj.block_type in {PostBlock.BlockType.IMAGE, PostBlock.BlockType.IMAGE_PAIR}:
            url = obj.get_image_url()
            if not url:
                return "-"
            return format_html(
                "<img src='{}' style='max-width:180px;max-height:100px;object-fit:cover;border-radius:6px;' alt='preview'>",
                url,
            )
        return "-"

    block_preview.short_description = "Preview"


class PostAdminForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={"rows": 18}), required=False)

    class Meta:
        model = Post
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        upload_url = None
        try:
            upload_url = reverse("vorin_blog:tinymce_image_upload")
        except NoReverseMatch:
            upload_url = None
        self.fields["content"].widget = _build_content_widget(upload_url)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    inlines = [PostBlockInline, PostImageInline]
    list_display = [
        "cover_preview",
        "title",
        "status",
        "show_on_homepage",
        "category",
        "published_label",
        "views",
    ]
    list_display_links = ["cover_preview", "title"]
    list_editable = ["status", "show_on_homepage"]
    list_filter = ["status", "show_on_homepage", "category", "created_at"]
    search_fields = ["title", "excerpt", "content"]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ["tags"]
    ordering = ["-published_at", "-id"]
    date_hierarchy = "created_at"
    readonly_fields = [
        "current_featured_image_display",
        "current_header_image_display",
        "views",
        "created_at",
        "updated_at",
    ]
    fieldsets = (
        ("Post Info", {"fields": ("title", "slug", "excerpt", "content")}),
        (
            "Images",
            {
                "fields": (
                    "current_featured_image_display",
                    "featured_image_file",
                    "featured_image",
                    "featured_image_alt",
                    "current_header_image_display",
                    "header_image_file",
                    "header_image",
                )
            },
        ),
        ("Categorization", {"fields": ("category", "tags")}),
        ("Publishing", {"fields": ("status", "is_featured", "show_on_homepage", "published_at")}),
        ("SEO", {"fields": ("meta_title", "meta_description", "canonical_url"), "classes": ("collapse",)}),
        ("System", {"fields": ("original_url", "views", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def cover_preview(self, obj):
        if not obj.featured_image:
            return "-"
        return format_html(
            "<img src='{}' style='width:72px;height:48px;object-fit:cover;border-radius:6px;' alt='cover'>",
            obj.featured_image,
        )

    cover_preview.short_description = "Cover"

    def published_label(self, obj):
        return _format_datetime(obj.published_at)

    published_label.short_description = "Published"
    published_label.admin_order_field = "published_at"

    def current_featured_image_display(self, obj):
        if not obj.featured_image:
            return format_html("<em>No thumbnail image set.</em>")
        return format_html(
            "<img src='{}' style='max-width:320px;max-height:220px;object-fit:contain;border-radius:8px;' alt='featured image'>",
            obj.featured_image,
        )

    current_featured_image_display.short_description = "Current thumbnail"

    def current_header_image_display(self, obj):
        image_url = obj.get_header_image()
        if not image_url:
            return format_html("<em>No header image set.</em>")
        return format_html(
            "<img src='{}' style='max-width:420px;max-height:140px;object-fit:cover;border-radius:8px;' alt='header image'>",
            image_url,
        )

    current_header_image_display.short_description = "Current header image"
