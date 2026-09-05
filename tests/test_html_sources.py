from ai_daily_brief.sources.html import parse_listing


def test_parse_listing_extracts_matching_article_links():
    page = """
    <html><a href='/news/model-release'>Model release</a>
    <a href='/about'>About</a><a href='/news/model-release'>Duplicate</a></html>
    """

    items = parse_listing(page, "anthropic_blog", "https://example.com/news", r"/news/")

    assert len(items) == 1
    assert items[0].title == "Model release"
    assert items[0].url == "https://example.com/news/model-release"
