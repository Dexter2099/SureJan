from django import template

register = template.Library()


@register.filter
def can_author_delete(post, user):
    """Return True if the post's author can delete within the allowed window."""
    return post.can_author_delete(user, 15)
