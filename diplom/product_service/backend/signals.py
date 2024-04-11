from typing import Type
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created
from backend.tasks import task_new_user, task_new_order, task_password_reset
from backend.models import ConfirmEmailToken, User

new_user_registered = Signal()

new_order = Signal()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token,
                                 **kwargs):
    """
        Отправляем письмо с токеном для сброса пароля
    """
    task_password_reset.delay(reset_password_token.user_id)


@receiver(post_save, sender=User)
def new_user_registered_signal(sender: Type[User], instance: User,
                               created: bool, **kwargs):
    """
    отправляем письмо с подтрердждением почты
    """

    if created and not instance.is_active:
        task_new_user.delay(instance.pk)


@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    """
    отправяем письмо при изменении статуса заказа
    """
    task_new_order.delay(user_id)
