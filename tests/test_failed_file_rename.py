from pathlib import Path

import pytest

from mdcx.base import file as base_file
from mdcx.core import file as core_file
from mdcx.models.types import FileInfo


def _failed_file_info(number: str, name: str) -> FileInfo:
    fi = FileInfo.empty()
    fi.number = number
    fi.file_path = Path(f"/movies/{name}")
    fi.file_name = name.rsplit(".", 1)[0]
    return fi


def test_generate_failed_file_name_uses_recognized_number(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(core_file.manager.config, "success_file_rename", True)
    monkeypatch.setattr(core_file.manager.config, "main_mode", 1)
    monkeypatch.setattr(core_file.manager.config, "naming_file", "{{ number }}")
    monkeypatch.setattr(core_file.manager.config, "file_name_max", 255)
    monkeypatch.setattr(core_file.manager.config, "prevent_char", "")

    fi = _failed_file_info("ABC-123", "bbs2048.org@ABC-123-1080p.mp4")

    assert core_file.generate_failed_file_name(fi) == "ABC-123"


def test_generate_failed_file_name_falls_back_to_original_when_no_number(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(core_file.manager.config, "success_file_rename", True)
    monkeypatch.setattr(core_file.manager.config, "main_mode", 1)
    monkeypatch.setattr(core_file.manager.config, "naming_file", "{{ number }}")
    monkeypatch.setattr(core_file.manager.config, "file_name_max", 255)
    monkeypatch.setattr(core_file.manager.config, "prevent_char", "")

    fi = _failed_file_info("", "unidentified-clip.mp4")

    # 无法识别番号时回退为原文件名（不含扩展名），不会破坏文件
    assert core_file.generate_failed_file_name(fi) == "unidentified-clip"


@pytest.mark.asyncio
async def test_move_file_to_failed_folder_applies_new_name(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(base_file.manager.config, "main_mode", 1)
    monkeypatch.setattr(base_file.manager.config, "failed_file_move", 1)
    monkeypatch.setattr(base_file.manager.config, "soft_link", 0)

    src = tmp_path / "src"
    src.mkdir()
    movie = src / "bbs2048.org@ABC-123-1080p.mp4"
    movie.write_bytes(b"x")
    failed = tmp_path / "failed"

    result = await base_file.move_file_to_failed_folder(failed, movie, src, new_file_name="ABC-123")

    assert result == failed / "ABC-123.mp4"
    assert (failed / "ABC-123.mp4").exists()
    assert not movie.exists()


@pytest.mark.asyncio
async def test_move_file_to_failed_folder_keeps_name_without_new_name(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(base_file.manager.config, "main_mode", 1)
    monkeypatch.setattr(base_file.manager.config, "failed_file_move", 1)
    monkeypatch.setattr(base_file.manager.config, "soft_link", 0)

    src = tmp_path / "src"
    src.mkdir()
    movie = src / "original-name.mp4"
    movie.write_bytes(b"x")
    failed = tmp_path / "failed"

    result = await base_file.move_file_to_failed_folder(failed, movie, src)

    assert result == failed / "original-name.mp4"
    assert (failed / "original-name.mp4").exists()
