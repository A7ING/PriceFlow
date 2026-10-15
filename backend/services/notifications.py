import asyncio
import html
import os
import re
import smtplib
from dataclasses import dataclass
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

TELEGRAM_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_TIMEOUT = 20
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")


def format_price(value) -> str:
    try:
        return f"{float(value):.2f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(value)


def _mask(text) -> str:
    s = str(text)
    return s.replace(TELEGRAM_BOT_TOKEN, "***") if TELEGRAM_BOT_TOKEN else s


@dataclass
class Alert:
    method: str
    contact: str
    subject: str
    text: str
    image_url: str | None = None


def build_price_alert(settings, name, url, image_url, old_price, new_price) -> Alert | None:
    """Формує повідомлення про зміну ціни з урахуванням налаштувань. None = слати не треба."""
    if not settings or not settings.contact_info or not old_price or not new_price or new_price == old_price:
        return None

    safe_name = html.escape(name or "")
    safe_url = html.escape(url or "", quote=True)

    if new_price < old_price:
        if not settings.notify_drop:
            return None
        text = (
            f"<b>PRICE DROP ALERT!</b>\n\n"
            f"<b>{safe_name}</b>\n"
            f"Old price: <s>{format_price(old_price)} UAH</s>\n"
            f"New price: <b>{format_price(new_price)} UAH</b>\n"
            f"Discount: <b>{format_price(old_price - new_price)} UAH</b>\n\n"
            f"<a href='{safe_url}'><b>View Product</b></a>"
        )
    else:
        if not settings.notify_rise:
            return None
        text = (
            f"<b>PRICE INCREASE ALERT!</b>\n\n"
            f"<b>{safe_name}</b>\n"
            f"Old price: <s>{format_price(old_price)} UAH</s>\n"
            f"New price: <b>{format_price(new_price)} UAH</b>\n\n"
            f"<a href='{safe_url}'><b>View Product</b></a>"
        )

    return Alert(settings.notify_method, settings.contact_info, "PriceFlow Alert!", text, image_url)


async def send_alert(alert: Alert) -> bool:
    if alert.method == "telegram":
        return await send_telegram_message(alert.contact, alert.text, alert.image_url)
    if alert.method == "email":
        return await send_email_message(alert.contact, alert.subject, alert.text, alert.image_url)
    print(f"[сповіщення] Невідомий метод: {alert.method}", flush=True)
    return False


async def send_telegram_message(chat_id: str, text: str, image_url: str = None) -> bool:
    chat_id = (chat_id or "").strip()
    if not re.fullmatch(r"-?\d+", chat_id):
        print("[телеграм] Невірний формат Chat ID.", flush=True)
        return False
    if not TELEGRAM_BOT_TOKEN:
        print("[телеграм] Не задано TG_BOT_TOKEN.", flush=True)
        return False

    base = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = None

            if image_url and len(text) <= 1024:
                response = await client.post(
                    f"{base}/sendPhoto",
                    data={"chat_id": chat_id, "photo": image_url, "caption": text, "parse_mode": "HTML"},
                )
                if response.status_code != 200:
                    print("[телеграм] Не вдалося відправити фото, відправляємо як текст.", flush=True)

            if response is None or response.status_code != 200:
                response = await client.post(
                    f"{base}/sendMessage",
                    data={"chat_id": chat_id, "text": text[:4096], "parse_mode": "HTML"},
                )

            if response.status_code == 200:
                print(f"[телеграм] Повідомлення відправлено на {chat_id}", flush=True)
                return True
            print(f"[телеграм] Помилка API: {response.text[:300]}", flush=True)
            return False
    except Exception as e:
        print(f"[телеграм] Критична помилка: {_mask(e)}", flush=True)
        return False


def _send_smtp_sync(msg) -> None:
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)


async def send_email_message(to_email: str, subject: str, html_content: str, image_url: str = None) -> bool:
    if not to_email or "@" not in to_email:
        print("[EMAIL] Невірний формат пошти.", flush=True)
        return False
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("[EMAIL] Не задано SENDER_EMAIL / SENDER_PASSWORD.", flush=True)
        return False

    try:
        msg = MIMEMultipart("related")
        msg["From"] = f"PriceFlow Alerts <{SENDER_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        formatted_body = html_content.replace("\n", "<br>")
        img_tag = ""
        image_data = None

        if image_url:
            try:
                async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                    response = await client.get(image_url)
                    if response.status_code == 200:
                        image_data = response.content
                        img_tag = (
                            '<div style="text-align: center; margin-top: 20px;">'
                            '<img src="cid:product_image" alt="Product Image" '
                            'style="max-width: 300px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">'
                            "</div>"
                        )
            except Exception as e:
                print(f"[EMAIL] Не вдалося завантажити картинку для листа: {e}", flush=True)

        full_html = f"""
        <html>
            <body style="font-family: sans-serif; color: #333; background-color: #f4f7f6; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #eee; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <div style="font-size: 16px; line-height: 1.5;">
                        {formatted_body}
                    </div>
                    {img_tag}
                </div>
            </body>
        </html>
        """

        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)
        msg_alternative.attach(MIMEText(full_html, "html"))

        if image_data:
            image = MIMEImage(image_data)
            image.add_header("Content-ID", "<product_image>")
            image.add_header("Content-Disposition", "inline", filename="product.jpg")
            msg.attach(image)

        await asyncio.wait_for(asyncio.to_thread(_send_smtp_sync, msg), timeout=SMTP_TIMEOUT * 3)

        print(f"[EMAIL] Лист успішно відправлено на {to_email}", flush=True)
        return True
    except Exception as e:
        print(f"[EMAIL] Помилка відправки: {str(e)}", flush=True)
        return False