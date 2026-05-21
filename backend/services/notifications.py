import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import httpx

TELEGRAM_BOT_TOKEN = "8640781340:AAFumIcgm9AKgqFahY9OIWAxjlyqs5ubKI8"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "priceflow.alerts@gmail.com"
SENDER_PASSWORD = "duauqdukdiqmkibd"


async def send_email_message(to_email: str, subject: str, html_content: str, image_url: str = None):
    if not to_email or "@" not in to_email:
        print("[EMAIL] Невірний формат пошти.")
        return False

    try:
        msg = MIMEMultipart('related')
        msg["From"] = f"PriceFlow Alerts <{SENDER_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        formatted_body = html_content.replace("\n", "<br>")
        img_tag = ""
        image_data = None

        if image_url:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url)
                    if response.status_code == 200:
                        image_data = response.content
                        img_tag = f'<div style="text-align: center; margin-top: 20px;"><img src="cid:product_image" alt="Product Image" style="max-width: 300px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"></div>'
            except Exception as e:
                print(f"[EMAIL] Не вдалося завантажити картинку для листа: {e}")

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

        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        msg_alternative.attach(MIMEText(full_html, "html"))

        if image_data:
            image = MIMEImage(image_data)
            image.add_header('Content-ID', '<product_image>')
            image.add_header('Content-Disposition', 'inline', filename='product.jpg')
            msg.attach(image)

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"[EMAIL] Лист успішно відправлено на {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Помилка відправки: {str(e)}")
        return False