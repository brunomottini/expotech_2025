import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os


def enviar_mail_confirmacion(
    mail_contacto: str,
):
    """
    Envía un correo con un logo incluido al final del mensaje.

    Parámetros:
    - mail_contacto (str): Correo del destinatario.
    """

    sender_email = "bruno@dsinergia.com"
    sender_password = "zpcl xoii tiyt lwyj"
    logo_path = os.path.join(os.getcwd(), "static", "empresas", "visnai_logo.png")
    subject = "Confirmacion de contacto"
    body = "Este es un mensaje de conformacion!. En breve una persona se contactara para darte mas informacion!!!"

    # Crear el correo
    message = MIMEMultipart("related")
    message["From"] = sender_email
    message["To"] = mail_contacto
    message["Subject"] = subject

    # Cuerpo del correo con HTML para incluir la imagen
    html_body = f"""
    <html>
        <body>
            <p>{body}</p>
            <br>
           <p>Equipo Visnai</p>
                <img src="cid:logo" alt="Logo de la empresa" style="width:150px; height:auto;">
        </body>
    </html>
    """

    # Adjuntar cuerpo HTML
    message.attach(MIMEText(html_body, "html"))

    # Adjuntar el logo como imagen
    try:
        with open(logo_path, "rb") as logo_file:
            mime_logo = MIMEBase("image", "png", filename="visnai_logo.png")
            mime_logo.set_payload(logo_file.read())
            encoders.encode_base64(mime_logo)
            mime_logo.add_header("Content-ID", "<logo>")
            mime_logo.add_header(
                "Content-Disposition", "inline", filename="visnai_logo.png"
            )
            message.attach(mime_logo)
    except Exception as e:
        print(f"Error al adjuntar el logo: {e}")
        return "No se pudo adjuntar el logo al correo."

    # Enviar el correo
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, mail_contacto, message.as_string())
        print(f"Correo enviado con éxito a {mail_contacto}")
    except smtplib.SMTPAuthenticationError:
        print(
            "Error de autenticación: Verifica tus credenciales o la configuración de seguridad de tu cuenta."
        )
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
