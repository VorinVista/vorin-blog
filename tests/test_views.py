from django.test import TestCase, override_settings
from django.urls import reverse

from vorin_blog.models import Category, Post


class BlogViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Guides")
        self.post = Post.objects.create(
            title="Published Post",
            excerpt="A short summary",
            content="<p>Hello world</p>",
            category=self.category,
            status=Post.Status.PUBLISHED,
            show_on_homepage=True,
        )
        Post.objects.create(
            title="Draft Post",
            content="<p>Draft</p>",
            status=Post.Status.DRAFT,
        )

    def test_list_view_shows_only_published_posts(self):
        response = self.client.get(reverse("vorin_blog:post_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Post")
        self.assertNotContains(response, "Draft Post")

    def test_detail_view_increments_views(self):
        response = self.client.get(reverse("vorin_blog:post_detail", kwargs={"slug": self.post.slug}))

        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.views, 1)

    @override_settings(VORIN_BLOG_EXTRA_CONTEXT_CALLBACK="tests.callbacks.blog_context")
    def test_extra_context_callback_is_applied(self):
        response = self.client.get(reverse("vorin_blog:post_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["callback_marker"], "from-post_list")

    def test_category_view_filters_posts(self):
        response = self.client.get(reverse("vorin_blog:category_detail", kwargs={"slug": self.category.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Post")
