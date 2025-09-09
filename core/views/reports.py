"""Reporting-related views."""

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from ..models import Post, Report
from comments.models import Comment
from ..utils.view_helpers import _is_banned


@login_required
@require_http_methods(["GET", "POST"])
@csrf_protect
def report(request):
    """Allow users to report posts or comments."""
    if _is_banned(request.user):
        return HttpResponseForbidden("Account banned")

    if request.method == "POST":
        target_type = request.POST.get("target_type")
        object_id = request.POST.get("object_id")
        mode = request.POST.get("mode")
    else:
        target_type = request.GET.get("target_type")
        object_id = request.GET.get("object_id")
        mode = request.GET.get("mode")

    is_note = mode == "note"
    if is_note and not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")

    if target_type not in {"post", "comment"}:
        return HttpResponseBadRequest("Invalid target")

    try:
        object_id = int(object_id)
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid object id")

    model = Post if target_type == "post" else Comment
    target_qs = model.objects.filter(is_deleted=False) if model is Post else model.objects.all()
    target = get_object_or_404(target_qs, pk=object_id)

    if request.method == "POST":
        reason = request.POST.get("reason", "")
        Report.objects.create(
            reporter=request.user,
            content_type=ContentType.objects.get_for_model(target),
            object_id=target.pk,
            reason=reason,
            is_note=is_note,
        )
        return render(request, "core/report_form.html", {"thanks": True, "mode": mode})

    return render(
        request,
        "core/report_form.html",
        {"target": target, "target_type": target_type, "object_id": object_id, "mode": mode},
    )


@staff_member_required
def report_list(request):
    """Simple listing view for recent reports."""
    reports = Report.objects.select_related("reporter", "content_type").order_by("-created_at")
    return render(request, "core/report_list.html", {"reports": reports})
