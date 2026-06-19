import asyncio
import re
from pathlib import Path
from urllib.parse import quote, urljoin

import aiofiles
from bs4 import BeautifulSoup

from ..config.manager import manager
from ..signals import signal

BASE_URL = "https://www.subtitlecat.com"
SEARCH_URL = f"{BASE_URL}/index.php"
# 简体中文优先, 其次繁体中文
CHINESE_LANG_CODES = ("zh-CN", "zh-TW")
_SUBTITLE_LINK_RE = re.compile(r"/?subs/\d+/.*\.html")
_SUBTITLE_ID_RE = re.compile(r"/?subs/(\d+)/")
_REQUEST_DELAY = 1.0


def _rank_candidates(html: str, number: str) -> str | None:
    """从搜索结果页选择最佳字幕详情页 URL.

    优先级: 标题需包含番号; 其次按来源语言排序, 中文 > 英文 > 其它.
    返回详情页 URL, 未找到返回 None.
    """
    soup = BeautifulSoup(html, "lxml")
    links = soup.find_all("a", href=_SUBTITLE_LINK_RE)
    if not links:
        return None

    number_lower = number.lower()
    candidates: list[tuple[int, int, str]] = []
    for idx, link in enumerate(links[:20]):
        href = link.get("href")
        if not href or not _SUBTITLE_ID_RE.search(href):
            continue
        link_text = link.get_text(strip=True)
        if number_lower not in link_text.lower():
            continue
        parent_text = link.parent.get_text().lower() if link.parent else ""
        if "translated from chinese" in parent_text:
            priority = 0
        elif "translated from english" in parent_text:
            priority = 1
        else:
            priority = 2
        candidates.append((priority, idx, urljoin(BASE_URL, href)))

    if not candidates:
        return None
    candidates.sort(key=lambda c: (c[0], c[1]))
    return candidates[0][2]


def _select_chinese_srt_links(html: str) -> list[str]:
    """从字幕详情页解析中文 .srt 下载链接, 简体优先."""
    soup = BeautifulSoup(html, "lxml")
    hrefs: list[str] = []
    for lang_code in CHINESE_LANG_CODES:
        links = soup.find_all("a", href=re.compile(rf".*-{re.escape(lang_code)}\.srt$"))
        if links:
            href = links[0].get("href")
            if href:
                hrefs.append(href)
    return hrefs


def build_subtitle_filename(file_name: str) -> str:
    """根据视频文件名(不含扩展名)生成字幕文件名. subtitlecat 仅提供 srt 格式."""
    suffix = ".chs.srt" if manager.config.subtitle_add_chs else ".srt"
    return file_name + suffix


async def _search_movie(number: str) -> str | None:
    client = manager.computed.async_client
    search_url = f"{SEARCH_URL}?search={quote(number)}"
    html, error = await client.get_text(search_url, encoding="utf-8")
    if not html:
        if error:
            signal.show_log_text(f"    ⚠️ 搜索失败 '{number}': {error}")
        return None
    return _rank_candidates(html, number)


async def _download_chinese_subtitle(subtitle_url: str, file_name: str, folder_path: Path) -> Path | None:
    client = manager.computed.async_client
    html, error = await client.get_text(subtitle_url, encoding="utf-8")
    if not html:
        if error:
            signal.show_log_text(f"    ⚠️ 字幕页访问失败: {error}")
        return None

    hrefs = _select_chinese_srt_links(html)
    if not hrefs:
        return None

    for href in hrefs:
        download_url = urljoin(BASE_URL, href)
        content, _ = await client.get_content(download_url)
        # 校验返回的是字幕而非错误页
        if content and content[:100].lower().find(b"<html") == -1:
            sub_path = folder_path / build_subtitle_filename(file_name)
            async with aiofiles.open(sub_path, "wb") as f:
                await f.write(content)
            return sub_path
        await asyncio.sleep(0.5)
    return None


async def download_subtitle_for_movie(number: str, file_name: str, folder_path: Path) -> Path | None:
    """为单部影片在线搜索并下载中文字幕, 成功返回保存路径, 否则返回 None."""
    if not number:
        return None
    subtitle_url = await _search_movie(number)
    if not subtitle_url:
        return None
    await asyncio.sleep(_REQUEST_DELAY)
    return await _download_chinese_subtitle(subtitle_url, file_name, folder_path)
