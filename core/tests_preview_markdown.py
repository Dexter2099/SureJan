from django.test import TestCase
from django.urls import reverse


class MarkdownPreviewViewTests(TestCase):
    def test_get_preview(self):
        resp = self.client.get(reverse('preview_markdown'), {'body': '**Hi**'}, HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<strong>Hi</strong>', resp.content.decode())

    def test_rejects_post(self):
        resp = self.client.post(reverse('preview_markdown'), {'body': 'Hi'}, HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 405)
