from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from ..models import Community, Post


class PostCreationTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        User = get_user_model()
        self.user = User.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.url = reverse("submit_post", args=[self.community.slug])
        self.client.login(username="alice", password="pwd")

    def test_body_only(self):
        resp = self.client.post(
            self.url,
            {
                "community": self.community.pk,
                "post_type": "text",
                "title": "Hello",
                "body": "Body",
            },
        )
        self.assertEqual(resp.status_code, 302)
        post = Post.objects.get()
        self.assertEqual(post.post_type, "text")
        self.assertEqual(post.body, "Body")
        self.assertEqual(post.content_url, "")

    def test_url_only(self):
        resp = self.client.post(
            self.url,
            {
                "community": self.community.pk,
                "post_type": "link",
                "title": "Link",
                "content_url": "https://example.com",
            },
        )
        self.assertEqual(resp.status_code, 302)
        post = Post.objects.get()
        self.assertEqual(post.post_type, "link")
        self.assertEqual(post.content_url, "https://example.com")
        self.assertEqual(post.body, "")

    def test_body_and_url(self):
        resp = self.client.post(
            self.url,
            {
                "community": self.community.pk,
                "post_type": "link",
                "title": "Both",
                "body": "Body",
                "content_url": "https://example.com",
            },
        )
        self.assertEqual(resp.status_code, 302)
        post = Post.objects.get()
        self.assertEqual(post.post_type, "link")
        self.assertEqual(post.body, "Body")
        self.assertEqual(post.content_url, "https://example.com")


class CommentFormTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        User = get_user_model()
        self.user = User.objects.create_user("alice", password="pwd")
        self.community = Community.objects.create(
            slug="t", name="Test", title="Test", created_by=self.user
        )
        self.post = Post.objects.create(
            community=self.community,
            author=self.user,
            post_type="text",
            title="Post",
            body="Body",
        )
        self.client.login(username="alice", password="pwd")

    def test_submit_comment(self):
        url = reverse("comment_reply", args=[self.post.pk])
        resp = self.client.post(url, {"body": "Nice"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.post.comments.count(), 1)
        comment = self.post.comments.get()
        self.assertEqual(comment.body, "Nice")
        self.assertEqual(comment.author, self.user)


class PreviewTests(TestCase):
    def test_strips_disallowed_tags_but_keeps_links(self):
        text = "Hello <script>alert(1)</script> [link](http://example.com)"
        resp = self.client.post(reverse("preview"), {"text": text})
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn('<a href="http://example.com">link</a>', html)
        self.assertNotIn("<script>", html)


def test_comment_ctrl_cmd_enter_submits(tmp_path):
    subprocess.run(
        ["npm", "init", "-y"], cwd=tmp_path, check=True, stdout=subprocess.DEVNULL
    )
    subprocess.run(
        ["npm", "install", "jsdom@22"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    script_path = Path(__file__).resolve().parents[2] / "static/js/editor.js"
    node_code = f"""
const {{JSDOM}} = require('jsdom');
const fs = require('fs');
const dom = new JSDOM(`<form><textarea></textarea></form>`, {{runScripts: 'outside-only'}});
const window = dom.window;
const textarea = window.document.querySelector('textarea');
let submitted = false;
const form = window.document.querySelector('form');
form.requestSubmit = () => {{ submitted = true; }};
const script = fs.readFileSync('{script_path}', 'utf8');
window.eval(script);
window.setupEditor(textarea);
function trigger(opts){{ textarea.dispatchEvent(new window.KeyboardEvent('keydown', opts)); }}
trigger({{key: 'Enter', ctrlKey: true}});
const ctrl = submitted;
submitted = false;
trigger({{key: 'Enter', metaKey: true}});
const meta = submitted;
console.log(ctrl && meta ? 'ok' : 'fail');
"""
    result = subprocess.run(
        ["node", "-e", node_code],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "ok" in result.stdout
