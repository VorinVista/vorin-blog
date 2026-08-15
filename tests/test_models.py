from django.test import TestCase

from vorin_blog.models import Category, Post


class PostModelTests(TestCase):
    def test_post_slug_is_unique(self):
        first = Post.objects.create(title="Same Title", status=Post.Status.PUBLISHED)
        second = Post.objects.create(title="Same Title", status=Post.Status.PUBLISHED)

        self.assertEqual(first.slug, "same-title")
        self.assertEqual(second.slug, "same-title-1")

    def test_category_slug_is_unique(self):
        first = Category.objects.create(name="Weddings")
        second = Category.objects.create(name="Weddings")

        self.assertEqual(first.slug, "weddings")
        self.assertEqual(second.slug, "weddings-1")
