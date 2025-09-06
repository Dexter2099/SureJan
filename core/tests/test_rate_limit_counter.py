from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited


class RateLimitTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("tester", password="pw")
        self.factory = RequestFactory()

    def dummy(self, request):
        return HttpResponse("ok")

    def test_limit_enforced(self):
        view = ratelimit(key="user", rate="2/60s", method=["POST"], block=True)(
            self.dummy
        )
        req = self.factory.post("/")
        req.user = self.user
        resp1 = view(req)
        self.assertEqual(resp1.status_code, 200)
        resp2 = view(req)
        self.assertEqual(resp2.status_code, 200)
        with self.assertRaises(Ratelimited):
            view(req)
