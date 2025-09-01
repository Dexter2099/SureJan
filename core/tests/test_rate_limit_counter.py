from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from core.models import RateLimitCounter
from core.ratelimit import ratelimit


class RateLimitCounterTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("tester", password="pw")
        self.factory = RequestFactory()

    def dummy(self, request):
        return HttpResponse("ok")

    def test_counter_enforced_and_persisted(self):
        view = ratelimit(action="test", limit=2, window=60)(self.dummy)
        req = self.factory.post("/")
        req.user = self.user
        resp1 = view(req)
        self.assertEqual(resp1.status_code, 200)
        resp2 = view(req)
        self.assertEqual(resp2.status_code, 200)
        resp3 = view(req)
        self.assertEqual(resp3.status_code, 429)
        counter = RateLimitCounter.objects.get(user=self.user, action="test")
        self.assertEqual(counter.count, 2)
