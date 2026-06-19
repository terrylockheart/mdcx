import pytest

from mdcx.base import file as base_file
from mdcx.config.enums import CleanAction


@pytest.mark.asyncio
async def test_movie_lists_auto_clean_false_keeps_junk_files(tmp_path, monkeypatch):
    junk = tmp_path / "ad.html"
    junk.write_text("x", encoding="utf-8")
    movie = tmp_path / "ABC-123.mp4"
    movie.write_bytes(b"x")

    monkeypatch.setattr(base_file.manager.config, "clean_enable", [CleanAction.AUTO_CLEAN])
    monkeypatch.setattr(base_file, "need_clean", lambda p, f, e: e == ".html")

    result = await base_file.movie_lists([], [".mp4"], tmp_path, auto_clean=False)

    assert junk.exists()  # 关闭自动清理时不应删除文件
    assert movie in result


@pytest.mark.asyncio
async def test_movie_lists_auto_clean_true_removes_junk_files(tmp_path, monkeypatch):
    junk = tmp_path / "ad.html"
    junk.write_text("x", encoding="utf-8")
    movie = tmp_path / "ABC-123.mp4"
    movie.write_bytes(b"x")

    monkeypatch.setattr(base_file.manager.config, "clean_enable", [CleanAction.AUTO_CLEAN])
    monkeypatch.setattr(base_file, "need_clean", lambda p, f, e: e == ".html")

    result = await base_file.movie_lists([], [".mp4"], tmp_path, auto_clean=True)

    assert not junk.exists()  # 默认开启自动清理时删除匹配文件
    assert movie in result
