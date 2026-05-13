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
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
                payload = {
                    "chat_id": chat_id,
                    "photo": image_url,
                    "caption": text,
                    "parse_mode": "HTML",
                }
            else:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
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


async def send_email_message(to_email: str, subject: str, html_content: str):
    """Функція для відправки листів через SMTP"""
    if not to_email or "@" not in to_email:
        print("[EMAIL] Невірний формат пошти.")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = f"PriceFlow Alerts <{SENDER_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        # Конвертуємо перенесення рядків у HTML-теги для красивого листа
        formatted_html = html_content.replace("\n", "<br>")
        msg.attach(MIMEText(formatted_html, "html"))

        # Використовуємо захищене SSL з'єднання
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"[EMAIL] Лист успішно відправлено на {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Помилка відправки: {str(e)}")
        return False
