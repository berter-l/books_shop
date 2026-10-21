from celery import Celery
from smtplib import SMTP_SSL
from email.message import EmailMessage

celery_email_app = Celery(broker="amqp://guest:guest@rabbitmq:5672/")


@celery_email_app.task(name="send_email")
def send_email(message: str, user_email: str):
    """
    Отправляет письмо на указанную почту пользователя с указанным сообщением.
    Args:
        message: сообщение, которое нужно отправить пользователю в письме.
        user_email: почта пользователя, которому нужно отправить письмо.

    Returns:
        - None.
    """

    # Формируем письмо, которое отправит пользователю.
    letter = EmailMessage()
    letter["From"] = "Почта, которая будет указана в отправителях."
    letter["To"] = user_email
    letter["Subject"] = "Уведомление от магазина книг."
    letter.set_content(message)

    # Открываем соединение с smtp сервером, проходит аутентификацию и отправлят письмо от email приложения.
    with SMTP_SSL(
        host="Сюда нужно вставить адрес почтового сервера SMTP.", port=465
    ) as smtp:

        smtp.login(
            "Почта, которая будет указана в отправителях.",
            "Пароль приложения для почты.",
        )

        smtp.send_message(letter)

    return None
