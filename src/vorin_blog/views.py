from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.text import get_valid_filename
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .conf import get_extra_context, get_setting
from .content_utils import normalize_post_content
from .models import Category, Post, Tag


def _base_context():
    return {
        "blog_base_template": get_setting("BASE_TEMPLATE"),
    }


@csrf_exempt
@staff_member_required
@require_POST
def tinymce_image_upload(request):
    upload = request.FILES.get("file")
    if not upload:
        return JsonResponse({"error": "No file uploaded."}, status=400)

    content_type = upload.content_type or ""
    if not content_type.startswith("image/"):
        return JsonResponse({"error": "Only image uploads are allowed."}, status=400)

    safe_name = get_valid_filename(upload.name)
    timestamp_path = datetime.utcnow().strftime("%Y/%m")
    target_path = f"uploads/vorin_blog/editor/{timestamp_path}/{safe_name}"

    saved_path = default_storage.save(target_path, upload)
    file_url = default_storage.url(saved_path)
    if not file_url.startswith(("http", "/")):
        file_url = f"/{file_url}"

    return JsonResponse({"location": file_url})


def post_list(request):
    posts = Post.objects.published().select_related("category").prefetch_related("tags")
    category_slug = request.GET.get("category")
    tag_slug = request.GET.get("tag")
    query = request.GET.get("q")

    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)
    if query:
        posts = posts.filter(
            Q(title__icontains=query)
            | Q(excerpt__icontains=query)
            | Q(content__icontains=query)
        ).distinct()

    paginator = Paginator(posts, get_setting("POSTS_PER_PAGE"))
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        **_base_context(),
        "posts": page_obj,
        "categories": Category.objects.all(),
        "tags": Tag.objects.all(),
        "featured_posts": Post.objects.published()
        .filter(show_on_homepage=True)
        .order_by("-published_at", "-id")[: get_setting("FEATURED_POSTS_LIMIT")],
        "active_category_slug": category_slug,
        "active_tag_slug": tag_slug,
        "query": query or "",
    }
    context.update(get_extra_context(request, "post_list"))
    return render(request, "vorin_blog/post_list.html", context)


def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.published().select_related("category").prefetch_related("tags", "blocks", "images"),
        slug=slug,
    )
    Post.objects.filter(pk=post.pk).update(views=F("views") + 1)
    post.views += 1

    related_posts = Post.objects.published().filter(category=post.category).exclude(pk=post.pk)
    if post.category is None:
        related_posts = Post.objects.published().exclude(pk=post.pk)

    context = {
        **_base_context(),
        "post": post,
        "post_content_html": normalize_post_content(post.content),
        "related_posts": related_posts.order_by("-published_at", "-id")[: get_setting("RELATED_POSTS_LIMIT")],
    }
    context.update(get_extra_context(request, "post_detail", post=post))
    return render(request, "vorin_blog/post_detail.html", context)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.published().filter(category=category).select_related("category")
    paginator = Paginator(posts, get_setting("POSTS_PER_PAGE"))
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        **_base_context(),
        "category": category,
        "posts": page_obj,
        "categories": Category.objects.all(),
    }
    context.update(get_extra_context(request, "category_detail", category=category))
    return render(request, "vorin_blog/category.html", context)
