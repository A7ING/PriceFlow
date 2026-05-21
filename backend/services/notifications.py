import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import httpx

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
        image_subtype = "jpeg"

        if image_url:
            try:
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                    "Referer": "https://www.google.com/",
                }
                async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
                    response = await client.get(image_url, headers=headers)

                    content_type = response.headers.get("content-type", "")
                    print(f"[EMAIL] Картинка статус: {response.status_code}, content-type: {content_type}")

                    if response.status_code == 200 and "image" in content_type:
                        image_data = response.content

                        if "png" in content_type:
                            image_subtype = "png"
                        elif "webp" in content_type:
                            image_subtype = "webp"
                        elif "gif" in content_type:
                            image_subtype = "gif"
                        else:
                            image_subtype = "jpeg"

                        img_tag = (
                            '<div style="text-align: center; margin-top: 20px;">'
                            '<img src="cid:product_image" alt="Product Image" '
                            'style="max-width: 300px; border-radius: 8px; '
                            'box-shadow: 0 4px 6px rgba(0,0,0,0.1);">'
                            '</div>'
                        )
                        print(f"[EMAIL] Картинка завантажена успішно ({len(image_data)} байт, {image_subtype})")
                    else:
                        print(f"[EMAIL] Не вдалося отримати картинку: status={response.status_code}, type={content_type}")

            except Exception as e:
                print(f"[EMAIL] Помилка завантаження картинки: {e}")

        full_html = f"""
        <html>
            <body style="font-family: sans-serif; color: #333; background-color: #f4f7f6; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;
                            border: 1px solid #eee; padding: 25px; border-radius: 12px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
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
            image = MIMEImage(image_data, _subtype=image_subtype)
            image.add_header('Content-ID', '<product_image>')
            image.add_header('Content-Disposition', 'inline', filename=f'product.{image_subtype}')
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