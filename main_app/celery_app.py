from celery import Celery

celery_app = Celery(broker="amqp://guest:guest@rabbitmq:5672/")

# Параметр который указывает, что все задачи send_email отправляются в очередь emails.
celery_app.conf.task_routes = {"send_email": {"queue": "emails"}}
