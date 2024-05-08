from typing import Type
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created
from backend.tasks import task_new_user, task_new_order, task_password_reset, \
    file_update, task_update_photo
from backend.models import ConfirmEmailToken, User, Product

new_user_registered = Signal()

new_order = Signal()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token,
                                 **kwargs):
    """ Отправляем письмо с токеном для сброса пароля """
    task_password_reset.delay(reset_password_token.user_id)


@receiver(post_save, sender=User)
def new_user_registered_signal(sender: Type[User], instance: User,
                               created: bool, **kwargs):
    """ Отправляем письмо с подтрердждением почты """

    if created and not instance.is_active:
        task_new_user.delay(instance.pk)
    else:
        file_update.delay(instance.pk, instance.avatar_thumbnail.name)


@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    """ Отправяем письмо при изменении статуса заказа """
    task_new_order.delay(user_id)


@receiver(post_save, sender=Product)
def product_photo_update(sender: Type[Product], instance: Product,
                         created: bool, **kwargs):
    """ Обновление фото продукта """
    if not created:
        task_update_photo.delay(instance.pk, instance.product_photo.name)
