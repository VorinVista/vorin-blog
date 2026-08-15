from django.urls import include, path


urlpatterns = [
    path("blog/", include(("vorin_blog.urls", "vorin_blog"), namespace="vorin_blog")),
]
