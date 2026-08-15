# vorin-blog

Reusable installable Django blog app, built to live in GitHub and be reused across future Django projects.

## Why this variant won

After comparing the blog apps across the projects in `C:\Users\telis\Django`, the best base was the richer `blog` family found in:

- `PhotaPy/StudioTool/blog`
- `Aneliza/blog`
- `AnelizePhotography/blog`
- `PhotaPy/PhotographerPlatform/blog`
- `PhotaPy/PhP1/blog`

It won because it already had:

- categories and tags
- SEO fields
- structured content blocks
- legacy HTML support for imported WordPress posts
- stronger Django admin UX
- featured and header images

The simpler `PhotaPy0.1/0.3.0` apps were cleaner but much less capable, while `Boring/backend/apps/blog` was Wagtail-specific and not appropriate as a general-purpose Django app.

## Features

- installable Django app
- categories, tags, publishing states, SEO metadata
- block-based post builder
- optional legacy HTML content cleanup
- TinyMCE-first admin editing
- built-in templates and CSS
- sitemap support

## Install

```bash
pip install -e .
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "tinymce",
    "vorin_blog",
]
```

Include URLs:

```python
from django.urls import include, path

urlpatterns = [
    path("blog/", include(("vorin_blog.urls", "vorin_blog"), namespace="vorin_blog")),
]
```

Run migrations:

```bash
python manage.py migrate
```

## Optional settings

```python
VORIN_BLOG_BASE_TEMPLATE = "base.html"
VORIN_BLOG_POSTS_PER_PAGE = 6
VORIN_BLOG_RELATED_POSTS_LIMIT = 3
VORIN_BLOG_FEATURED_POSTS_LIMIT = 3
VORIN_BLOG_EXTRA_CONTEXT_CALLBACK = "myproject.blog_context.blog_context"
```

The optional callback must return a dictionary and receives:

- `request`
- `view_name`
- optionally `post` or `category`

## Template strategy

By default the app renders with its own internal base template:

- `vorin_blog/base.html`

If you set `VORIN_BLOG_BASE_TEMPLATE = "base.html"`, the provided templates will extend your project template instead. In that case you will usually also want to either:

- override the blog templates in your project, or
- include the package CSS manually

## Included templates

- `vorin_blog/post_list.html`
- `vorin_blog/post_detail.html`
- `vorin_blog/category.html`

## Included sitemap

```python
from vorin_blog.sitemaps import PostSitemap

sitemaps = {
    "blog": PostSitemap,
}
```
