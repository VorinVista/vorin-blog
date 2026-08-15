from django.contrib.auth import get_user_model
from django.utils import timezone

from vorin_blog.models import Category, Post, PostBlock, Tag


User = get_user_model()


def create_superuser():
    username = "admin"
    password = "admin12345!"
    email = "admin@example.com"
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
    return username, password


def seed():
    weddings, _ = Category.objects.get_or_create(
        name="Weddings",
        defaults={"description": "Stories, planning ideas, and visual inspiration."},
    )
    seo, _ = Category.objects.get_or_create(
        name="SEO",
        defaults={"description": "Content strategy and search visibility ideas."},
    )
    tips, _ = Tag.objects.get_or_create(name="Tips")
    showcase, _ = Tag.objects.get_or_create(name="Showcase")
    tinymce, _ = Tag.objects.get_or_create(name="TinyMCE")

    visual_post, created = Post.objects.get_or_create(
        slug="welcome-to-vorin-blog",
        defaults={
            "title": "Welcome to Vorin Blog",
            "excerpt": "A block-based sample post for checking the richer editorial flow.",
            "status": Post.Status.PUBLISHED,
            "show_on_homepage": True,
            "is_featured": True,
            "category": weddings,
            "published_at": timezone.now(),
        },
    )
    visual_post.tags.set([tips, showcase, tinymce])
    if created:
        PostBlock.objects.create(
            post=visual_post,
            block_type=PostBlock.BlockType.INTRO,
            order=1,
            body_text=(
                "This demo post exists so we can inspect the reading flow, the typography, "
                "and the TinyMCE-first editing experience without depending on any old project."
            ),
        )
        PostBlock.objects.create(
            post=visual_post,
            block_type=PostBlock.BlockType.TEXT,
            order=2,
            heading="Why this matters",
            body_text=(
                "A reusable blog app should feel comfortable both for the editor in the admin "
                "and for the visitor reading the article.\n\n"
                "This block-based mode gives us a more directed layout when we want stronger storytelling."
            ),
        )
        PostBlock.objects.create(
            post=visual_post,
            block_type=PostBlock.BlockType.QUOTE,
            order=3,
            quote_text="The writing interface should invite creativity instead of fighting it.",
            quote_author="Vorin Blog demo",
        )

    html_post, _ = Post.objects.get_or_create(
        slug="tinymce-legacy-html-demo",
        defaults={
            "title": "TinyMCE and Legacy HTML Demo",
            "excerpt": "A second sample post showing the legacy HTML content rendering path.",
            "content": (
                "<h2>Editing freedom matters</h2>"
                "<p>TinyMCE is the main editor here because it gives the post author more creative freedom.</p>"
                "<p>You can mix paragraphs, headings, links, and images in a way that feels natural.</p>"
                "<figure><img src=\"https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=1200&q=80\" alt=\"Laptop on a desk\"></figure>"
                "<p>This also lets us test the HTML cleanup path for imported or handcrafted content.</p>"
            ),
            "status": Post.Status.PUBLISHED,
            "show_on_homepage": True,
            "category": seo,
            "published_at": timezone.now(),
        },
    )
    html_post.tags.set([tips, tinymce])

    username, password = create_superuser()
    print(f"Demo ready. Admin login: {username} / {password}")


seed()
