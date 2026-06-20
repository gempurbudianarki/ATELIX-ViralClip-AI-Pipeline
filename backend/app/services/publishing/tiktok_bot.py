"""
ATELIX ViralClip AI Pipeline — TikTok Publishing Bot
Autonomous publisher using Playwright with stealth for TikTok uploads.
"""

import asyncio
import random
import time
from pathlib import Path
from typing import Optional

from app.core.config import get_settings

settings = get_settings()


def publish_to_tiktok(
    clip_id: str,
    video_path: str,
    caption: str,
    hashtags: list[str],
) -> dict:
    """
    Publish a rendered clip to TikTok using browser automation.

    Uses Playwright with stealth plugin to avoid bot detection.
    Implements human-like delays and behavior patterns.
    """
    from app.core.database import async_session_factory
    from app.models import Clip, PipelineStatus
    from sqlalchemy import select

    async def _update_status(status: PipelineStatus):
        async with async_session_factory() as session:
            result = await session.execute(select(Clip).where(Clip.id == clip_id))
            clip = result.scalar_one_or_none()
            if clip:
                clip.status = status
                await session.commit()

    asyncio.get_event_loop().run_until_complete(
        _update_status(PipelineStatus.PUBLISHING)
    )

    try:
        result = asyncio.get_event_loop().run_until_complete(
            _upload_via_playwright(clip_id, video_path, caption, hashtags)
        )

        async def _save_success():
            async with async_session_factory() as session:
                result_query = await session.execute(
                    select(Clip).where(Clip.id == clip_id)
                )
                clip = result_query.scalar_one_or_none()
                if clip:
                    clip.status = PipelineStatus.COMPLETED
                    clip.tiktok_url = result.get("tiktok_url", "")
                    await session.commit()

        asyncio.get_event_loop().run_until_complete(_save_success())

        return result

    except Exception as e:
        async def _save_error():
            async with async_session_factory() as session:
                result = await session.execute(select(Clip).where(Clip.id == clip_id))
                clip = result.scalar_one_or_none()
                if clip:
                    clip.status = PipelineStatus.FAILED
                    clip.error_message = f"Publishing failed: {str(e)}"
                    await session.commit()

        asyncio.get_event_loop().run_until_complete(_save_error())
        raise


async def _upload_via_playwright(
    clip_id: str,
    video_path: str,
    caption: str,
    hashtags: list[str],
) -> dict:
    """
    Core Playwright automation for TikTok upload.

    Steps:
    1. Launch stealth browser
    2. Login to TikTok
    3. Navigate to upload page
    4. Upload video file
    5. Fill caption + hashtags
    6. Publish or schedule
    """
    from playwright.async_api import async_playwright

    if not settings.tiktok_username or not settings.tiktok_password:
        raise ValueError("TikTok credentials not configured. Set TIKTOK_USERNAME and TIKTOK_PASSWORD in .env")

    video_path_abs = str(Path(video_path).resolve())

    if not Path(video_path_abs).exists():
        raise FileNotFoundError(f"Video file not found: {video_path_abs}")

    full_caption = _format_caption(caption, hashtags)

    async with async_playwright() as p:
        launch_args = {
            "headless": settings.tiktok_headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        }

        if settings.tiktok_proxy:
            launch_args["proxy"] = {"server": settings.tiktok_proxy}

        browser = await p.chromium.launch(**launch_args)

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )

        try:
            page = await context.new_page()

            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => false });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            """)

            await _tiktok_login(page)

            await _human_delay(2, 4)

            await page.goto("https://www.tiktok.com/upload", wait_until="domcontentloaded")
            await _human_delay(3, 5)

            await _upload_video_file(page, video_path_abs)

            await _human_delay(5, 8)

            await _fill_caption(page, full_caption)

            await _human_delay(2, 3)

            await _click_publish(page)

            await _human_delay(5, 10)

            tiktok_url = await _get_post_url(page)

            return {
                "clip_id": clip_id,
                "status": "published",
                "tiktok_url": tiktok_url,
                "caption": caption,
                "hashtags": hashtags,
            }

        finally:
            await browser.close()


async def _tiktok_login(page):
    """
    Handle TikTok login with human-like typing and delays.
    """
    await page.goto("https://www.tiktok.com/login", wait_until="domcontentloaded")
    await _human_delay(2, 3)

    try:
        await page.click('button:has-text("Use phone / email / username")', timeout=5000)
    except Exception:
        pass

    await _human_delay(1, 2)

    await page.click('a:has-text("Log in with email or username")', timeout=3000)
    await _human_delay(1, 2)

    username_input = await page.wait_for_selector('input[name="username"]', timeout=5000)
    if username_input:
        await username_input.click()
        await _human_type(username_input, settings.tiktok_username)

    await _human_delay(0.5, 1)

    password_input = await page.wait_for_selector('input[type="password"]', timeout=5000)
    if password_input:
        await password_input.click()
        await _human_type(password_input, settings.tiktok_password)

    await _human_delay(1, 2)

    try:
        await page.click('button:has-text("Log in")', timeout=5000)
    except Exception:
        pass

    await _human_delay(5, 8)


async def _upload_video_file(page, video_path: str):
    """
    Handle the file upload input (usually hidden).
    """
    try:
        file_input = await page.wait_for_selector('input[type="file"]', timeout=15000)
        await file_input.set_input_files(video_path)
    except Exception as e:
        raise RuntimeError(f"Failed to upload video file: {e}")


async def _fill_caption(page, full_caption: str):
    """
    Fill the caption field with human-like typing (optional: just paste for speed).
    """
    try:
        caption_div = await page.wait_for_selector(
            '[contenteditable="true"], div[data-placeholder="Add caption"]',
            timeout=10000,
        )
        if caption_div:
            await caption_div.click()
            await _human_delay(0.3, 1)
            await page.keyboard.type(full_caption, delay=random.randint(10, 40))
    except Exception:
        pass


async def _click_publish(page):
    """
    Click the publish/submit button.
    """
    try:
        await page.click('button:has-text("Post")', timeout=10000)
    except Exception:
        try:
            await page.click('div:has-text("Post")', timeout=5000)
        except Exception as e:
            raise RuntimeError(f"Failed to click publish button: {e}")


async def _get_post_url(page) -> str:
    """
    Attempt to extract the published post URL.
    """
    try:
        await page.wait_for_url("**/video/*", timeout=30000)
        current_url = page.url
        if "/video/" in current_url:
            return current_url
    except Exception:
        pass

    return ""


def _format_caption(caption: str, hashtags: list[str]) -> str:
    """
    Format caption with hashtags for TikTok.
    TikTok caption limit: 2200 characters.
    """
    hashtag_str = " ".join(
        f"#{tag.strip().replace('#', '').replace(' ', '')}" for tag in hashtags[:20]
    )

    full = f"{caption}\n\n{hashtag_str}"

    return full[:2200]


async def _human_delay(min_seconds: float, max_seconds: float):
    """Add random delay to simulate human behavior."""
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)


async def _human_type(element, text: str):
    """Type text with random delays between keystrokes."""
    for char in text:
        await element.type(char, delay=random.randint(50, 150))
    await asyncio.sleep(random.uniform(0.2, 0.5))
