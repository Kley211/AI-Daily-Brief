from datetime import timezone

from ai_daily_brief.sources.rss import parse_feed


RSS = b"""
<rss version="2.0"><channel>
  <item>
    <guid>post-1</guid><title>New model release</title>
    <link>https://example.com/post-1</link>
    <pubDate>Fri, 05 Sep 2026 00:00:00 GMT</pubDate>
    <description><![CDATA[<p>A short <b>summary</b>.</p>]]></description>
  </item>
  <item><title>Missing link</title><description>Ignored</description></item>
</channel></rss>
"""


def test_parse_rss_feed_returns_normalized_item():
    items = parse_feed(RSS, "openai_blog")

    assert len(items) == 1
    assert items[0].source_id == "openai_blog"
    assert items[0].external_id == "post-1"
    assert items[0].title == "New model release"
    assert items[0].content_excerpt == "A short summary."
    assert items[0].published_at.tzinfo == timezone.utc


def test_parse_atom_feed_supports_namespaces():
    atom = b"""
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry><id>a-1</id><title>Atom post</title>
        <link href="https://example.com/a-1"/>
        <updated>2026-09-05T00:00:00Z</updated>
        <summary>Atom summary</summary>
      </entry>
    </feed>
    """

    items = parse_feed(atom, "anthropic_blog")

    assert len(items) == 1
    assert items[0].url == "https://example.com/a-1"
    assert items[0].content_excerpt == "Atom summary"
