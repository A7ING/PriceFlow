import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import httpx

TELEGRAM_BOT_TOKEN = "8640781340:AAFumIcgm9AKgqFahY9OIWAxjlyqs5ubKI8"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "priceflow.alerts@gmail.com"
SENDER_PASSWORD = "duauqdukdiqmkibd"


async def send_telegram_message(chat_id: str, text: str, image_url: str = None):
    if not chat_id or not chat_id.isdigit():
        print("[телеграм] Невірний формат Chat ID.")


return False

async with httpx.AsyncClient() as client:
    try:
        if image_url:
            url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){TELEGRAM_BOT_TOKEN}/sendPhoto"
            payload = {
                "chat_id": chat_id,
                "photo": image_url,
                "caption": text,
                "parse_mode": "HTML",
            }
        else:
            url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

        response = await client.post(url, json=payload)
        if response.status_code == 200:
            print(f"[телеграм] Повідомлення відправлено на {chat_id}")
            return True
        else:
            print(f"[телеграм] Помилка API: {response.text}")
            return False
    except Exception as e:
        print(f"[телеграм] Помилка: {str(e)}")
        return False


async def send_email_message(to_email: str, subject: str, html_content: str, image_url: str = None):
    if not to_email or "@" not in to_email:
        print("[EMAIL] Невірний формат пошти.")


return False

try:
    msg = MIMEMultipart()
    msg["From"] = f"PriceFlow Alerts <{SENDER_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject

    formatted_body = html_content.replace("\n", "<br>")

    if image_url:
        full_html = f"""
        <html>
            <body style="font-family: sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
                    <div style="margin-bottom: 20px;">
                        {formatted_body}
                    </div>
                    <div style="text-align: center;">
                        <img src="{image_url}" alt="Product Image" style="max-width: 300px; border-radius: 8px;">
                    </div>
                </div>
            </body>
        </html>
        """
    else:
        full_html = f"<html><body>{formatted_body}</body></html>"

    msg.attach(MIMEText(full_html, "html"))

    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)
    server.quit()

    print(f"[EMAIL] Лист успішно відправлено на {to_email}")
    return True
except Exception as e:
    print(f"[EMAIL] Помилка відправки: {str(e)}")
    return False