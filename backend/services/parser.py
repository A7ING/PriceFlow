import asyncio
import re
from urllib.parse import quote, urlparse

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

MAX_CONCURRENT_PARSERS = asyncio.Semaphore(1)

STORE_SELECTORS = {
    "rozetka.com.ua": {
        "name": ["h1.product__title", "h1.qa-product-title", ".product__header h1"],
        "price": [
            "p.product-prices__big",
            ".product-price__big",
            ".product-prices__main",
        ],
    },
    "prom.ua": {
        "name": ["[data-qaid='product_name']", "h1", ".x-product-info__name"],
        "price": [
            "[data-qaid='product_price']",
            ".cabinet-price",
            "[data-testid='price']",
            ".x-product-info__price",
        ],
    },
    "allo.ua": {
        "name": ["h1.p-view__header-title", "h1"],
        "price": [".v-pb__cur", ".p-trade__price-new .sum", "[data-price-amount]"],
    },
    "housebrand.com": {
        "name": ["h1[data-selen='product-name']", ".product-name", "h1", "h2"],
        "price": ["div[data-selen='product-price']", ".price-promo", ".price-standard"],
    },
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def clean_price(raw_price) -> float:
    if raw_price is None:
        return 0.0

    if isinstance(raw_price, (int, float)):
        return float(raw_price)

    try:
        text = str(raw_price)
        text = text.replace("\xa0", "")
        text = text.replace(" ", "")
        text = text.replace(",", ".")

        clean_str = re.sub(r"[^\d.]", "", text)

        return float(clean_str) if clean_str else 0.0

    except:
        return 0.0


async def extract_price_from_dom(page):
    possible_containers = [
        "main",
        ".product",
        ".product-page",
        ".product-main",
        ".product-card",
        "[itemtype='http://schema.org/Product']",
        "[itemtype='https://schema.org/Product']",
        "#content",
        "body",
    ]

    money_pattern = r"(\d[\d\s,.]*)\s?" r"(?:₴|грн|UAH|€|\$|zł|PLN|Kč|CZK|£)"
    for selector in possible_containers:
        try:
            container = await page.query_selector(selector)
            if not container:
                continue
            text = await container.inner_text()
            matches = re.findall(money_pattern, text, re.IGNORECASE)
            if not matches:
                continue
            valid_prices = [
                clean_price(m) for m in matches if 10 < clean_price(m) < 1000000
            ]
            if valid_prices:
                return max(valid_prices)
        except:
            continue
    return None


async def get_product_data(url: str):
    domain = urlparse(url).netloc.replace("www.", "")
    clean_url = url.split("?")[0]

    async with MAX_CONCURRENT_PARSERS:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            context = await browser.new_context(
                user_agent=USER_AGENT,
                locale="uk-UA",
                viewport={"width": 1920, "height": 1080},
                java_script_enabled=True,
            )
            await context.add_init_script("""
                Object.defineProperty(
                    navigator,
                    'webdriver',
                    {get: () => undefined}
                )
            """)
            page = await context.new_page()
            await stealth_async(page)

            try:
                print(f"[парсер] Завантаження: {domain}")
                await page.goto(clean_url, wait_until="domcontentloaded", timeout=25000)

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

                meta_price = re.search(
                    r'property="(?:product|og):price:amount" content="([\d.]+)"',
                    content,
                )
                if meta_price:
                    raw_price = meta_price.group(1)

                if not raw_price:
                    json_ld_price = re.search(r'"price":\s?"?([\d.]+)"?', content)
                    if json_ld_price:
                        raw_price = json_ld_price.group(1)

                if not raw_price and domain in STORE_SELECTORS:
                    rules = STORE_SELECTORS[domain]
                    for sel in rules["price"]:
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

                h1 = await page.query_selector("h1")
                if h1:
                    product_name = await h1.inner_text()
                elif domain in STORE_SELECTORS:
                    for sel in STORE_SELECTORS[domain]["name"]:
                        try:
                            el = await page.query_selector(sel)
                            if el:
                                product_name = await el.inner_text()
                                break
                        except:
                            continue

                if not product_name:
                    product_name = "Unknown Product"

                product_image = None
                img_selectors = [
                    'meta[property="og:image"]',
                    'meta[itemprop="image"]',
                    'img[itemprop="image"]',
                    "img#globalImage",
                    'img[data-qaid="image_preview"]',
                    "img.x-gallery__img",
                    "img.product-image",
                    'link[rel="image_src"]',
                ]

                for img_sel in img_selectors:
                    try:
                        img_el = await page.query_selector(img_sel)
                        if not img_el:
                            continue
                        tag_name = await img_el.evaluate(
                            "el => el.tagName.toLowerCase()"
                        )
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

                            if product_image.startswith("http"):
                                break
                    except:
                        continue

                final_price = clean_price(raw_price)
                if final_price == 0:
                    raise ValueError(
                        "Price not found (possibly CAPTCHA, Out of stock or anti-bot protection)"
                    )

                print(f"[парсер] Успіх: {final_price}")
                return {
                    "name": product_name.strip(),
                    "price": final_price,
                    "image_url": product_image,
                }

            except Exception as e:
                print(f"[парсер ERROR] {domain}: {str(e)}")
                raise e
            finally:
                await browser.close()