import asyncio
import html
import json
import os
import re
import sys
from urllib.parse import quote

from browserforge.fingerprints import Screen
from camoufox.async_api import AsyncCamoufox
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from services.stores import STORE_SELECTORS, is_heavy_guard, match_store

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def log(message: str) -> None:
    print(message, flush=True)


def clean_price(raw_price) -> float:
    if raw_price is None:
        return 0.0
    if isinstance(raw_price, (int, float)):
        return float(raw_price)
    try:
        text = str(raw_price).replace("\xa0", "").replace(" ", "").replace(",", ".")
        clean_str = re.sub(r"[^\d.]", "", text)
        return float(clean_str) if clean_str else 0.0
    except Exception:
        return 0.0


async def extract_price_from_dom(page):
    possible_containers = ["main", ".product", ".product-page", ".product-main", ".product-card", "#content", "body"]
    money_pattern = r"(\d[\d\s,.]*)\s?(?:₴|грн|UAH|€|\$|zł|PLN|Kč|CZK|£)"
    for selector in possible_containers:
        try:
            container = await page.query_selector(selector)
            if not container:
                continue
            text = await container.inner_text()
            matches = re.findall(money_pattern, text, re.IGNORECASE)
            valid_prices = [clean_price(m) for m in matches if 10 < clean_price(m) < 1000000]
            if valid_prices:
                return max(valid_prices)
        except Exception:
            continue
    return None


async def _extract_product_info(page, host: str, store):
    selectors = STORE_SELECTORS.get(store) if store else None

    wait_selector = "h1"
    wait_timeout = 8000
    if selectors:
        wait_selector = ", ".join(selectors["price"])
        wait_timeout = 12000

    try:
        await page.wait_for_selector(wait_selector, timeout=wait_timeout)
    except Exception:
        pass

    content = await page.content()
    product_name = None
    raw_price = None

    if selectors:
        for sel in selectors["price"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    if store == "prom.ua":
                        attr = await el.get_attribute("data-qaprice")
                        if attr:
                            raw_price = attr
                            break
                    text = await el.inner_text()
                    if text and text.strip():
                        raw_price = text.strip()
                        break
            except Exception:
                continue

    if not raw_price:
        meta_price = re.search(r'property="(?:product|og):price:amount" content="([\d.]+)"', content)
        if meta_price:
            raw_price = meta_price.group(1)

    if not raw_price:
        for m in re.finditer(r'"price":\s?"?([\d.]+)"?', content):
            if clean_price(m.group(1)) > 0:
                raw_price = m.group(1)
                break

    if not raw_price:
        raw_price = await extract_price_from_dom(page)

    await asyncio.sleep(1)

    meta_og = re.search(r'property="og:title" content="([^"]+)"', content)
    if meta_og:
        title = html.unescape(meta_og.group(1))
        product_name = re.split(r"\s*\|\s*|\s+[\-–—]\s+", title, maxsplit=1)[0].strip()

    if not product_name and selectors:
        for sel in selectors["name"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    text = await page.evaluate("(element) => element.innerText", el)
                    if text and text.strip():
                        product_name = text.strip()
                        break
            except Exception:
                continue

    if not product_name:
        try:
            h1 = await page.query_selector("h1")
            if h1:
                text = await page.evaluate("(element) => element.innerText", h1)
                if text and text.strip():
                    product_name = text.strip()
        except Exception:
            pass

    if not product_name:
        product_name = "Unknown Product"

    product_image = None
    img_selectors = [
        'meta[property="og:image"]',
        'link[rel="image_src"]',
        '[data-qaid="image_link"] img',
        ".gallery__image",
        'img[itemprop="image"]',
        "img.product-image",
        "img#globalImage",
    ]

    for img_sel in img_selectors:
        product_image = None
        try:
            img_el = await page.query_selector(img_sel)
            if not img_el:
                continue

            tag_name = await img_el.evaluate("el => el.tagName.toLowerCase()")
            if tag_name == "meta":
                product_image = await img_el.get_attribute("content")
            elif tag_name == "link":
                product_image = await img_el.get_attribute("href")
            else:
                product_image = await img_el.get_attribute("src")
                if not product_image or product_image.startswith("data:image"):
                    product_image = await img_el.get_attribute("data-src")

            if product_image:
                product_image = product_image.strip()

                if product_image.startswith("//"):
                    product_image = "https:" + product_image
                elif product_image.startswith("/"):
                    product_image = f"https://{host}{product_image}"
                elif not product_image.startswith("http"):
                    product_image = f"https://{host}/{product_image}"

                product_image = quote(product_image, safe=":/%?=&")

                if ".webp" in product_image.lower():
                    product_image = product_image.replace(".webp", ".jpg").replace(".WEBP", ".jpg")

                if product_image.startswith("http"):
                    break
        except Exception:
            continue

    if product_image and not product_image.startswith("http"):
        product_image = None

    final_price = clean_price(raw_price)
    if final_price == 0:
        raise ValueError("Price not found (possibly CAPTCHA or anti-bot protection)")

    return {"name": product_name.strip(), "price": final_price, "image_url": product_image}


async def run_parsers(clean_url: str, host: str, store, on_result):
    result = None

    if not is_heavy_guard(host):
        try:
            log(f"[парсер] Спроба 1 (Playwright): {host}")
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-disk-cache",
                    ],
                )
                try:
                    context = await browser.new_context(
                        user_agent=USER_AGENT, locale="uk-UA", viewport={"width": 1920, "height": 1080}
                    )
                    page = await context.new_page()
                    await stealth_async(page)
                    await page.goto(clean_url, wait_until="domcontentloaded", timeout=25000)
                    result = await _extract_product_info(page, host, store)
                    log(f"[парсер] Успіх Playwright: {result['price']}")
                    on_result(result)
                finally:
                    await browser.close()
        except Exception as e:
            if result is None:
                log(f"[парсер] Playwright не впорався ({e}). Запуск резервного обходу Camoufox")
            else:
                log(f"[парсер] Помилка при закритті Playwright (ігноруємо): {e}")
        if result is not None:
            return result

    try:
        log(f"[парсер] Спроба 2 (Camoufox): {host}")
        async with AsyncCamoufox(
            headless=True,
            os=["macos"],
            screen=Screen(max_width=1920, max_height=1080),
        ) as browser:
            page = await browser.new_page()
            await page.goto(clean_url, wait_until="domcontentloaded", timeout=35000)

            clicked = False
            for _ in range(15):
                await asyncio.sleep(1)
                for frame in page.frames:
                    if frame.url.startswith("https://challenges.cloudflare.com"):
                        try:
                            frame_element = await frame.frame_element()
                            bounding_box = await frame_element.bounding_box()
                            if bounding_box:
                                checkbox_x = bounding_box["x"] + bounding_box["width"] / 9
                                checkbox_y = bounding_box["y"] + bounding_box["height"] / 2
                                await page.mouse.click(x=checkbox_x, y=checkbox_y)
                                log("[парсер] Зроблено фізичний клік по капчі")
                                clicked = True
                        except Exception:
                            pass
                if clicked:
                    await asyncio.sleep(4)
                    break

            result = await _extract_product_info(page, host, store)
            log(f"[парсер] Успіх Camoufox: {result['price']}")
            on_result(result)
    except Exception as e:
        if result is None:
            log(f"[парсер ERROR] Не вдалося обійти захист {host}: {e}")
            raise
        log(f"[парсер] Помилка при закритті Camoufox (ігноруємо): {e}")

    return result


async def main():
    clean_url, host, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    store = match_store(host)

    def write(payload: dict) -> None:
        tmp_path = out_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        os.replace(tmp_path, out_path)
    try:
        await run_parsers(clean_url, host, store, lambda data: write({"ok": True, "data": data}))
    except Exception as e:
        if not os.path.exists(out_path):
            write({"ok": False, "error": str(e)[:300]})

    sys.stdout.flush()
    os._exit(0)

if __name__ == "__main__":
    asyncio.run(main())