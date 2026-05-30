import asyncio
import re
from urllib.parse import quote, urlparse

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from camoufox.async_api import AsyncCamoufox
from browserforge.fingerprints import Screen

MAX_CONCURRENT_PARSERS = asyncio.Semaphore(1)

STORE_SELECTORS = {
    "rozetka.com.ua": {
        "name": ["h1.product__title", "h1.qa-product-title", ".product__header h1"],
        "price": ["p.product-prices__big", ".product-price__big", ".product-prices__main"],
    },
    "prom.ua": {
        "name": ["[data-qaid='product_name']", "h1", ".x-product-info__name"],
        "price": ["[data-qaid='product_price']", ".cabinet-price", "[data-testid='price']", ".x-product-info__price"],
    },
    "allo.ua": {
        "name": ["h1.p-view__header-title", "h1"],
        "price": [".a-product-price__current-price", ".v-pb__cur", ".p-trade__price-new .sum", "[data-price-amount]"],
    },
    "housebrand.com": {
        "name": ["h1[data-testid='product-name']", ".product-name", "h1", "h2"],
        "price": ["div[data-selen='product-price']", ".price-promo", ".price-standard"],
    },
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

def clean_price(raw_price) -> float:
    if raw_price is None: return 0.0
    if isinstance(raw_price, (int, float)): return float(raw_price)
    try:
        text = str(raw_price).replace("\xa0", "").replace(" ", "").replace(",", ".")
        clean_str = re.sub(r"[^\d.]", "", text)
        return float(clean_str) if clean_str else 0.0
    except:
        return 0.0

async def extract_price_from_dom(page):
    possible_containers = ["main", ".product", ".product-page", ".product-main", ".product-card", "#content", "body"]
    money_pattern = r"(\d[\d\s,.]*)\s?(?:₴|грн|UAH|€|\$|zł|PLN|Kč|CZK|£)"
    for selector in possible_containers:
        try:
            container = await page.query_selector(selector)
            if not container: continue
            text = await container.inner_text()
            matches = re.findall(money_pattern, text, re.IGNORECASE)
            valid_prices = [clean_price(m) for m in matches if 10 < clean_price(m) < 1000000]
            if valid_prices: return max(valid_prices)
        except:
            continue
    return None

async def _extract_product_info(page, domain):
    wait_selector = "h1"
    wait_timeout = 8000

    if domain in STORE_SELECTORS:
        wait_selector = ", ".join(STORE_SELECTORS[domain]["price"])
        wait_timeout = 12000

    try:
        await page.wait_for_selector(wait_selector, timeout=wait_timeout)
    except:
        pass

    content = await page.content()
    product_name = None
    raw_price = None

    meta_price = re.search(r'property="(?:product|og):price:amount" content="([\d.]+)"', content)
    if meta_price: raw_price = meta_price.group(1)

    if not raw_price:
        json_ld_price = re.search(r'"price":\s?"?([\d.]+)"?', content)
        if json_ld_price: raw_price = json_ld_price.group(1)

    if not raw_price and domain in STORE_SELECTORS:
        for sel in STORE_SELECTORS[domain]["price"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    text = await el.inner_text()
                    if text:
                        raw_price = text
                        break
            except:
                continue

    if not raw_price:
        raw_price = await extract_price_from_dom(page)

    # ПОШУК НАЗВИ (ОНОВЛЕНО)
    if domain in STORE_SELECTORS:
        for sel in STORE_SELECTORS[domain]["name"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    text = await el.text_content()
                    if text and text.strip():
                        product_name = text.strip()
                        break
            except:
                continue

    if not product_name:
        try:
            meta_title = await page.query_selector('meta[property="og:title"]')
            if meta_title:
                text = await meta_title.get_attribute("content")
                if text and text.strip():
                    product_name = text.strip().split('|')[0].split('-')[0].strip()
        except:
            pass

    if not product_name:
        try:
            h1 = await page.query_selector("h1")
            if h1:
                text = await h1.text_content()
                if text and text.strip():
                    product_name = text.strip()
        except:
            pass

    if not product_name:
        product_name = "Unknown Product"

    # ПОШУК ЗОБРАЖЕННЯ
    product_image = None
    img_selectors = ['meta[property="og:image"]', 'img#globalImage', "img.product-image", 'link[rel="image_src"]']
    for img_sel in img_selectors:
        try:
            img_el = await page.query_selector(img_sel)
            if not img_el: continue
            tag_name = await img_el.evaluate("el => el.tagName.toLowerCase()")
            if tag_name == "meta":
                product_image = await img_el.get_attribute("content")
            elif tag_name == "link":
                product_image = await img_el.get_attribute("href")
            else:
                product_image = await img_el.get_attribute("src")

            if product_image:
                if product_image.startswith("//"):
                    product_image = "https:" + product_image
                elif product_image.startswith("/"):
                    product_image = f"https://{domain}{product_image}"
                product_image = quote(product_image, safe=":/%?=&")
                if product_image.startswith("http"): break
        except:
            continue

    final_price = clean_price(raw_price)
    if final_price == 0:
        raise ValueError("Price not found (possibly CAPTCHA or anti-bot protection)")

    return {"name": product_name.strip(), "price": final_price, "image_url": product_image}

async def get_product_data(url: str):
    domain = urlparse(url).netloc.replace("www.", "")
    clean_url = url.split("?")[0]

    async with MAX_CONCURRENT_PARSERS:
        try:
            print(f"[парсер] Спроба 1 (Playwright): {domain}")
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
                )
                context = await browser.new_context(
                    user_agent=USER_AGENT, locale="uk-UA", viewport={"width": 1920, "height": 1080}
                )
                page = await context.new_page()
                await stealth_async(page)

                await page.goto(clean_url, wait_until="domcontentloaded", timeout=25000)
                data = await _extract_product_info(page, domain)

                await browser.close()
                print(f"[парсер] Успіх Playwright: {data['price']}")
                return data

        except Exception as e:
            print(f"[парсер] Playwright не впорався ({str(e)}). Запуск резервного обходу Camoufox")

        try:
            print(f"[парсер] Спроба 2 (Camoufox): {domain}")
            async with AsyncCamoufox(
                headless=True,
                os=["macos"],
                screen=Screen(max_width=1920, max_height=1080)
            ) as browser:
                page = await browser.new_page()
                await page.goto(clean_url, wait_until="domcontentloaded", timeout=35000)

                clicked = False
                for _ in range(15):
                    await asyncio.sleep(1)
                    for frame in page.frames:
                        if frame.url.startswith('https://challenges.cloudflare.com'):
                            try:
                                frame_element = await frame.frame_element()
                                bounding_box = await frame_element.bounding_box()
                                if bounding_box:
                                    coord_x = bounding_box['x']
                                    coord_y = bounding_box['y']
                                    width = bounding_box['width']
                                    height = bounding_box['height']

                                    checkbox_x = coord_x + width / 9
                                    checkbox_y = coord_y + height / 2

                                    await page.mouse.click(x=checkbox_x, y=checkbox_y)
                                    print("[парсер] Зроблено фізичний клік по капчі")
                                    clicked = True
                            except:
                                pass
                    if clicked:
                        await asyncio.sleep(4)
                        break

                data = await _extract_product_info(page, domain)
                print(f"[парсер] Успіх Camoufox: {data['price']}")
                return data

        except Exception as fallback_error:
            print(f"[парсер ERROR] Не вдалося обійти захист {domain}: {str(fallback_error)}")
            raise fallback_error