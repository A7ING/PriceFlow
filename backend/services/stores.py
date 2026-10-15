
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
    "mta.ua": {
        "name": ["h1.product__title", "h1", ".product-name"],
        "price": [".price__current", ".product-price", ".price", "[itemprop='price']", ".product-price__active"],
    },
}

HEAVY_GUARD_SITES = ("rozetka.com.ua", "allo.ua")

def _host_matches(host: str, domain: str) -> bool:
    return host == domain or host.endswith("." + domain)

def match_store(host: str):
    host = (host or "").lower()
    for domain in STORE_SELECTORS:
        if _host_matches(host, domain):
            return domain
    return None

def is_heavy_guard(host: str) -> bool:
    host = (host or "").lower()
    return any(_host_matches(host, d) for d in HEAVY_GUARD_SITES)