def blog_context(request, view_name, **kwargs):
    return {
        "callback_marker": f"from-{view_name}",
    }

