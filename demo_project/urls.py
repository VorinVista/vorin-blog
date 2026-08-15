from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def root_redirect(request):
    return redirect("vorin_blog:post_list")


urlpatterns = [
    path("", root_redirect, name="home"),
    path("admin/", admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
    path("blog/", include(("vorin_blog.urls", "vorin_blog"), namespace="vorin_blog")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

