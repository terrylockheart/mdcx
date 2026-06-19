import pytest

from mdcx.tools.subtitle import _dedupe_existing_paths
from mdcx.utils.file import build_file_name_index, find_file_from_index


@pytest.mark.asyncio
async def test_build_file_name_index_finds_subtitle_in_nested_folder(tmp_path):
    subtitle_folder = tmp_path / "字幕包"
    nested_folder = subtitle_folder / "maker" / "series"
    nested_folder.mkdir(parents=True)
    subtitle_path = nested_folder / "ABC-123.srt"
    subtitle_path.write_text("1\n", encoding="utf-8")

    file_name_index = await build_file_name_index(subtitle_folder)

    assert find_file_from_index(file_name_index, ("ABC-123.srt",)) == subtitle_path
    assert find_file_from_index(file_name_index, ("abc-123.srt",)) == subtitle_path


def test_dedupe_existing_paths_keeps_path_order(tmp_path):
    first = tmp_path / "first.mp4"
    second = tmp_path / "second.mp4"

    assert _dedupe_existing_paths([first, second, first]) == [first, second]


@pytest.mark.asyncio
async def test_build_file_name_index_caches_with_use_cache(tmp_path, monkeypatch):
    import mdcx.utils.file as uf

    folder = tmp_path / "subs"
    folder.mkdir()
    (folder / "ABC-123.srt").write_text("1\n", encoding="utf-8")

    uf.clear_file_name_index_cache()
    calls = {"n": 0}
    real_builder = uf._build_file_name_index_sync

    def counting_builder(f):
        calls["n"] += 1
        return real_builder(f)

    monkeypatch.setattr(uf, "_build_file_name_index_sync", counting_builder)

    first = await uf.build_file_name_index(folder, use_cache=True)
    second = await uf.build_file_name_index(folder, use_cache=True)

    assert calls["n"] == 1  # 第二次命中缓存, 不重复扫描
    assert first is second
    assert find_file_from_index(second, ("abc-123.srt",)) == folder / "ABC-123.srt"

    # 不使用缓存时每次都重新扫描
    await uf.build_file_name_index(folder, use_cache=False)
    assert calls["n"] == 2

    # 清空缓存后重新构建
    uf.clear_file_name_index_cache()
    await uf.build_file_name_index(folder, use_cache=True)
    assert calls["n"] == 3
