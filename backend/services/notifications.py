import smtplib
import base64
import httpx
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "priceflow.alerts@gmail.com"
SENDER_PASSWORD = "duauqdukdiqmkibd"

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
        img_tag = ""

        if image_url and image_url.startswith('http'):
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url, headers=headers, timeout=10.0)
                    if response.status_code == 200:
                        b64_image = base64.b64encode(response.content).decode('utf-8')
                        img_tag = f'<div style="text-align: center; margin-top: 20px;"><img src="data:image/jpeg;base64,{b64_image}" alt="Product" style="max-width: 300px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"></div>'
                        print("[EMAIL] Картинка успішно закодована в Base64.")
            except Exception as e:
                print(f"[EMAIL] Помилка завантаження картинки: {e}")

        full_html = f"""
        <html>
            <body style="font-family: sans-serif; background-color: #f4f7f6; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 25px; border-radius: 12px;">
                    {formatted_body}
                    {img_tag}
                </div>
            </body>
        </html>
        """

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