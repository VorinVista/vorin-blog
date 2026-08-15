from django.urls import path

from . import views


app_name = "vorin_blog"

urlpatterns = [
    path("admin/tinymce-image-upload/", views.tinymce_image_upload, name="tinymce_image_upload"),
    path("", views.post_list, name="post_list"),
    path("post/<slug:slug>/", views.post_detail, name="post_detail"),
    path("category/<slug:slug>/", views.category_detail, name="category_detail"),
]
