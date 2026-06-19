import pytest

from mdcx.tools import subtitle_online


def test_rank_candidates_filters_by_title_match():
    html = """
    <html><body>
        <a href="/subs/111/UNRELATED-MOVIE.html">UNRELATED-MOVIE</a>
        <a href="/subs/222/SONE-991-something.html">SONE-991 something</a>
    </body></html>
    """
    assert (
        subtitle_online._rank_candidates(html, "SONE-991")
        == "https://www.subtitlecat.com/subs/222/SONE-991-something.html"
    )


def test_rank_candidates_prefers_chinese_source():
    html = """
    <html><body>
        <p>translated from english
            <a href="/subs/1/ABC-123-en.html">ABC-123 en</a>
        </p>
        <p>translated from chinese
            <a href="/subs/2/ABC-123-cn.html">ABC-123 cn</a>
        </p>
        <p>
            <a href="/subs/3/ABC-123-other.html">ABC-123 other</a>
        </p>
    </body></html>
    """
    assert subtitle_online._rank_candidates(html, "ABC-123") == "https://www.subtitlecat.com/subs/2/ABC-123-cn.html"


def test_rank_candidates_returns_none_without_match():
    html = '<html><body><a href="/subs/1/OTHER-1.html">OTHER-1</a></body></html>'
    assert subtitle_online._rank_candidates(html, "ABC-123") is None


def test_select_chinese_srt_links_prefers_simplified_first():
    html = """
    <html><body>
        <a href="/subs/1/movie-zh-TW.srt">繁体</a>
        <a href="/subs/1/movie-zh-CN.srt">简体</a>
        <a href="/subs/1/movie-en.srt">english</a>
    </body></html>
    """
    links = subtitle_online._select_chinese_srt_links(html)
    assert links == ["/subs/1/movie-zh-CN.srt", "/subs/1/movie-zh-TW.srt"]


def test_select_chinese_srt_links_empty_when_none():
    html = '<html><body><a href="/subs/1/movie-en.srt">english</a></body></html>'
    assert subtitle_online._select_chinese_srt_links(html) == []


def test_build_subtitle_filename_with_chs(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(subtitle_online.manager.config, "subtitle_add_chs", True)
    assert subtitle_online.build_subtitle_filename("ABC-123") == "ABC-123.chs.srt"


def test_build_subtitle_filename_without_chs(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(subtitle_online.manager.config, "subtitle_add_chs", False)
    assert subtitle_online.build_subtitle_filename("ABC-123") == "ABC-123.srt"
