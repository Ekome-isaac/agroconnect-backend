from rest_framework.views import exception_handler
from django.core.mail import send_mail

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "success": False,
            "errors": response.data
        }

    return response


def send_email_notification(subject, message, recipient_list):
    send_mail(
        subject=subject,
        message=message,
        from_email=None,  # uses DEFAULT_FROM_EMAIL
        recipient_list=recipient_list,
        fail_silently=False,
    )