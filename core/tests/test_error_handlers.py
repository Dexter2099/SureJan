from django.test import SimpleTestCase, override_settings
from django.urls import path

from core import views as core_views
from config.urls import urlpatterns as base_urlpatterns

urlpatterns = base_urlpatterns + [
    path("400/", core_views.handler400),
    path("403/", core_views.handler403),
    path("404/", core_views.handler404),
    path("500/", core_views.handler500),
    path("429/", core_views.handler429),
    path("413/", core_views.request_too_big),
]


@override_settings(ROOT_URLCONF=__name__)
class ErrorHandlerTests(SimpleTestCase):
    def _check(self, url, code):
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, code)
        self.assertTemplateUsed(resp, f"errors/{code}.html")
        resp = self.client.get(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, code)
        self.assertTemplateUsed(resp, f"errors/partials/{code}.html")

    def test_400(self):
        self._check("/400/", 400)

    def test_403(self):
        self._check("/403/", 403)

    def test_404(self):
        self._check("/404/", 404)

    def test_500(self):
        self._check("/500/", 500)

    def test_429(self):
        self._check("/429/", 429)

    def test_413(self):
        self._check("/413/", 413)
