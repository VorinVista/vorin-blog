from importlib import import_module

from django.conf import settings


DEFAULTS = {
    "BASE_TEMPLATE": "vorin_blog/base.html",
    "POSTS_PER_PAGE": 6,
    "RELATED_POSTS_LIMIT": 3,
    "FEATURED_POSTS_LIMIT": 3,
    "EXTRA_CONTEXT_CALLBACK": None,
}


def get_setting(name):
    return getattr(settings, f"VORIN_BLOG_{name}", DEFAULTS[name])


def import_string(dotted_path):
    module_path, attr_name = dotted_path.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, attr_name)


def get_extra_context(request, view_name, **kwargs):
    callback_path = get_setting("EXTRA_CONTEXT_CALLBACK")
    if not callback_path:
        return {}

    callback = import_string(callback_path)
    context = callback(request=request, view_name=view_name, **kwargs) or {}
    if not isinstance(context, dict):
        raise TypeError("VORIN_BLOG_EXTRA_CONTEXT_CALLBACK must return a dict.")
    return context
