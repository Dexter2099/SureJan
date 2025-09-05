from django.template import loader


def test_post_row_template_parses():
    loader.get_template("core/partials/post_row.html")


def test_comment_item_template_parses():
    loader.get_template("core/partials/comment_item.html")


def test_comment_row_template_parses():
    loader.get_template("core/partials/comment_row.html")


def test_post_detail_template_parses():
    loader.get_template("core/post_detail.html")


def test_feed_template_parses():
    loader.get_template("core/feed.html")
