from datetime import timedelta
from django.template import Context, Template
from django.test import TestCase
from django.utils import timezone


class WithinMinutesFilterTests(TestCase):
    def render(self, dt, minutes):
        tmpl = Template("{% load timeutils %}{{ dt|within_minutes:minutes }}")
        return tmpl.render(Context({"dt": dt, "minutes": minutes}))

    def test_within_minutes_true(self):
        dt = timezone.now() - timedelta(minutes=4)
        rendered = self.render(dt, 5)
        self.assertEqual(rendered, "True")

    def test_within_minutes_false(self):
        dt = timezone.now() - timedelta(minutes=6)
        rendered = self.render(dt, 5)
        self.assertEqual(rendered, "False")
