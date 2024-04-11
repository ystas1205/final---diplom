import yaml
import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django_rest_passwordreset.models import ResetPasswordToken
from product_service.celery import app
from backend.models import ConfirmEmailToken, User, Shop, Category, \
    ProductParameter, Parameter, ProductInfo, Product


@app.task
def task_new_user(user_id):
    """
    Отправляем письмо с подтрердждением почты
    """
    # UserModel = get_user_model()
    try:
        # user = UserModel.objects.get(pk=user_id)
        token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)
        send_mail(
            # title:
            f"Токен для {token.user}",
            # message:
            token.key,
            settings.EMAIL_HOST_USER,
            # from:
            [token.user.email],
            # to:
            fail_silently=False,
        )
    except ConfirmEmailToken.DoesNotExist:
        logging.warning(
            "Tried to send verification email to non-existing user '%s'" % user_id)
    return 'Done'


@shared_task
def task_password_reset(user_id):
    """
       Отправляем письмо для сброса пароля
    """
    try:
        data = ResetPasswordToken.objects.get(user_id=user_id)
        send_mail(
            # title:
            f"Токен сброса пароля для {data}",
            # message:
            data.key,
            # from:
            settings.EMAIL_HOST_USER,
            # to:
            [data.user.email],
            fail_silently=False,
        )
    except ResetPasswordToken.DoesNotExist:
        logging.warning(
            "Tried to send verification email to non-existing user '%s'" % user_id)
    return 'Done'


@shared_task
def task_new_order(user_id):
    """
       отправяем письмо при изменении статуса заказа
    """
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(pk=user_id)

        send_mail(
            # title:
            f"Обновление статуса заказа",
            # message:
            'Заказ сформирован',
            # from:
            settings.EMAIL_HOST_USER,
            # to:
            [user.email],
            fail_silently=False,
        )
    except UserModel.DoesNotExist:
        logging.warning(
            "Tried to send verification email to non-existing user '%s'" % user_id)
    return 'Done'


@shared_task
def task_product_export(user_id):
    """
        Задача для экспорта товаров из базы в файл
    """

    UserModel = get_user_model()
    user = UserModel.objects.get(pk=user_id)
    datas = Shop.objects.filter(state=True,
                                user_id=user.id, ).prefetch_related(
        'categories__products__product_infos__product_parameters__parameter')
    if datas:
        list_category = []
        list_goods = []
        for shops in datas:
            shop = shops.name
            for category in shops.categories.all():
                list_category.append({
                    'id': category.id,
                    'name': category.name
                })

                for product in category.products.all():
                    for product_info in product.product_infos.all():
                        dict_parameter = {}
                        for par in product_info.product_parameters.all():
                            dict_parameter.update(
                                {par.parameter.name: par.value})

                        list_goods.append({
                            'category': product.category_id,
                            'name': product.name,
                            'model': product_info.price,
                            'id': product_info.external_id,
                            'price': product_info.price,
                            'price_rrc': product_info.price_rrc,
                            'quantity': product_info.quantity,
                            'parameter': dict_parameter,

                        })

        data = {
            'shop': shop,
            'category': list_category,
            'goods': list_goods,
        }

        with open("product.yaml", "a", encoding='utf-8') as file:
            yaml.dump(data, file, allow_unicode=True, sort_keys=False)
        return 'Done'


@shared_task(bind=True)
def task_product_import(self, item, data, user_id, *args, **kwargs):
    """
    Задача для обновление базы данных
    """
    shop, _ = Shop.objects.get_or_create(name=data['shop'],
                                         user_id=user_id)
    for category in data['categories']:
        category_object, _ = Category.objects.get_or_create(
            id=category['id'], name=category['name'])
        category_object.shops.add(shop.id)
        category_object.save()
    ProductInfo.objects.filter(shop_id=shop.id).delete()
    for item in data['goods']:
        product, _ = Product.objects.get_or_create(
            name=item['name'], category_id=item['category'])

        product_info = ProductInfo.objects.create(
            product_id=product.id,
            external_id=item['id'],
            model=item['model'],
            price=item['price'],
            price_rrc=item['price_rrc'],
            quantity=item['quantity'],
            shop_id=shop.id)
        for name, value in item['parameters'].items():
            parameter_object, _ = Parameter.objects.get_or_create(
                name=name)
            ProductParameter.objects.create(
                product_info_id=product_info.id,
                parameter_id=parameter_object.id,
                value=value)
    return 'Done'
