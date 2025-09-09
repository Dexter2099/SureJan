from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from core.http import login_required_htmx
from core.models import Post
from comments.models import Comment
from votes.services import (
    AlreadyVoted,
    cast_vote_post_once,
    cast_vote_comment_once,
)


@require_POST
@login_required_htmx
def vote_post(request, pk):
    post = get_object_or_404(Post.objects.filter(is_deleted=False), pk=pk)

    try:
        want = int(request.POST["v"])
    except (KeyError, TypeError, ValueError):
        return HttpResponseBadRequest("Invalid vote")
    if want not in (1, -1):
        return HttpResponseBadRequest("Invalid vote")

    try:
        new_score = cast_vote_post_once(request.user, post, want)
    except AlreadyVoted:
        return HttpResponse(status=409)

    if request.headers.get("HX-Request") == "true":
        post.refresh_from_db()
        return render(
            request,
            "votes/partials/vote_widget.html",
            {"post": post, "voted": True},
        )

    return HttpResponse(f"<span id='post-{post.pk}-score'>{new_score}</span>")


@require_POST
@login_required_htmx
def vote_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    try:
        want = int(request.POST["v"])
    except (KeyError, TypeError, ValueError):
        return HttpResponseBadRequest("Invalid vote")
    if want not in (1, -1):
        return HttpResponseBadRequest("Invalid vote")

    try:
        new_score = cast_vote_comment_once(request.user, comment, want)
    except AlreadyVoted:
        return HttpResponse(status=409)

    if request.headers.get("HX-Request") == "true":
        comment.refresh_from_db()
        return render(
            request,
            "votes/partials/vote_widget.html",
            {"comment": comment, "voted": True},
        )

    return HttpResponse(
        f"<span id='comment-{comment.pk}-score'>{new_score}</span>"
    )
