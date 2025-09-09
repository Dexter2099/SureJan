"""Temporary shim for moved forms."""

# TODO: remove once callers import from app-specific modules
from comments.forms import CommentForm  # noqa: F401
from posts.forms import PostForm  # noqa: F401

__all__ = ["PostForm", "CommentForm"]

