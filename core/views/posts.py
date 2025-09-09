"""Temporary shim for moved post views."""

# TODO: remove once imports are updated to use posts.views directly
from posts.views import *  # noqa: F401,F403
from posts.views import _cached_post_signals  # noqa: F401

