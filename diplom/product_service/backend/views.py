from lib2to3.pgen2.parse import ParseError

from django.contrib.auth import get_user_model
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, \
    OpenApiExample, extend_schema_view, OpenApiResponse

from rest_framework import status
from backend.serializers import UserSerializer, ContactSerializer, Shop, \
    ProductInfoSerializer, OrderItemSerializer, ShopSerializer, \
    OrderSerializer, CategorySerializer
from backend.models import Contact, Shop, ConfirmEmailToken, ProductInfo, \
    Category, Product, Parameter, ProductParameter, Order, User, OrderItem
from distutils.util import strtobool

from rest_framework.request import Request
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError, ObjectDoesNotExist, \
    FieldDoesNotExist, EmptyResultSet
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from requests import get
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from ujson import loads as load_json
from yaml import load as load_yaml, Loader
from backend.signals import new_user_registered, new_order
from backend.tasks import task_product_export, task_product_import


class RegisterAccount(APIView):
    """
    Класс для регистрации покупателей
    """

    # Регистрация методом POST
    @extend_schema(
        summary="Регестрация пользователей",
        request=UserSerializer,
        examples=[
            OpenApiExample(
                "Post example",
                description="Test example for the post",
                value=
                {
                    "password": "",
                    "email": "ystas2019@mail.ru",
                    "company": "adidadas",
                    "position": "3231113",
                    "first_name": "Станислав",
                    "last_name": "Юдин"
                },
                # status_codes=[str(status.HTTP_201_CREATED)],
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        # проверяем обязательные аргументы
        # получаем почту с токеном
        if {'first_name', 'last_name', 'email', 'password', 'company',
            'position'}.issubset(request.data):
            # проверяем пароль на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse(
                    {'Status': False, 'Errors': {'password': error_array}})
            else:
                # проверяем данные для уникальности имени пользователя

                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    # сохраняем пользователя
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    return Response({'status': 'Регистрация прошла успешно'},
                                    status=status.HTTP_201_CREATED)
                else:
                    return JsonResponse(
                        {'Status': False, 'Errors': user_serializer.errors})

        return Response({'status': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)


class ConfirmAccount(APIView):
    """
    Класс для подтверждения почтового адреса
    """

    @extend_schema(
        summary="Подтверждения почтового адреса",
        request=UserSerializer,
        examples=[
            OpenApiExample(
                "Post example",
                description="Test example for the post",
                value=
                {
                    "email": "ystas2019@mail.ru",
                    "token": "00cdc7540e547f0dc7a03889815337bc27fa4dd",
                },
                # status_codes=[str(status.HTTP_200_OK)],
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        # проверяем обязательные аргументы
        if {'email', 'token'}.issubset(request.data):

            token = ConfirmEmailToken.objects.filter(
                user__email=request.data['email'],
                key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return Response({'status': 'Почтовый адрес подтвержден'},
                                status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'Status': 'Неправильно указан токен или email'},
                    status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)


class LoginAccount(APIView):
    """
    Класс для авторизации пользователей
    """

    # Авторизация методом POST
    @extend_schema(
        summary="Авторизация пользователей",
        request=UserSerializer,
        examples=[
            OpenApiExample(
                "Post example",
                description="Test example for the post",
                value=
                {
                    "email": "ystas2019@mail.ru",
                    "password": "8490866stas",
                },
                # status_codes=[str(status.HTTP_200_OK)],
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'],
                                password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)

                    return Response({'status': 'Авторизация прошла успешно',
                                     'Token': token.key})
            return Response({'status': 'Не удалось авторизовать'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)


class ContactView(APIView):
    """
    Класс для получения удаление добавление и замены контактных данных
    """

    @extend_schema(summary="Получение контакта")
    def get(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)
        contact = Contact.objects.filter(user=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Создание нового контакта",
        request=ContactSerializer,
        examples=[
            OpenApiExample(
                "Post example",
                description="Test example for the post",
                value=
                {
                    "city": "Gorod",
                    "street": "Shashkin street 40",
                    "house": "Apartament 28",
                    "structure": 123,
                    "building": 123,
                    "apartment": 123,
                    "phone": 89222334847,

                },
                # status_codes=[str(status.HTTP_200_OK)],
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)
        if {'city', 'street', 'phone'}.issubset(request.data):
            # request.data._mutable = True
            data = request.data.copy()
            data.update({'user': request.user.id})
            serializer = ContactSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response({'status': 'Контакты добавлены'},
                                status=status.HTTP_201_CREATED)
        return Response({'Status': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Обновление контакта",
        request=ContactSerializer,
        examples=[
            OpenApiExample(
                "Put example",
                description="Test example for the put",
                value=
                {"id": "2",
                 "city": "Gorod",
                 "street": "Shashkin street 40",
                 "house": "Apartament 28",
                 "structure": 1,
                 "building": 1,
                 "apartment": 123,
                 "phone": 89222334847,

                 },
                # status_codes=[str(status.HTTP_200_OK)],
            ),
        ],
    )
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)
        if 'id' in request.data:
            if request.data['id'].isdigit():
                contact = Contact.objects.filter(id=request.data['id'],
                                                 user_id=request.user.id).first()
                if contact:
                    serializer = ContactSerializer(contact, data=request.data)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                        return Response({'status': 'Контакты обновлены'},
                                        status=status.HTTP_201_CREATED)
        return Response({'Status': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Удаление контакта",
        request=ContactSerializer,
        examples=[
            OpenApiExample(
                "Put example",
                description="Test example for the put",
                value=
                {"items": 1,
                 },
                # status_codes=[str(status.HTTP_200_OK)],
            ),
        ],
    )
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)

        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True
                else:
                    return Response({'message': 'Введены некорректные данные'},
                                    status=status.HTTP_403_FORBIDDEN)

            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return Response(
                    {'message': f'Удалено {deleted_count}'},
                    status=status.HTTP_204_NO_CONTENT)
        return Response({'Status': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)


# your action behaviour

class ShopView(APIView):
    """
    Класс для получения списка магазинов
    """

    @extend_schema(summary="Получение списка магазинов")
    def get(self, request, *args, **kwargs):
        shop = Shop.objects.filter(state=True)
        serializer = ShopSerializer(shop, many=True)
        return Response(serializer.data)


class ProductInfoView(APIView):
    """
    Класс для поиска товаров.
    """

    @extend_schema(summary="Поиск товаров")
    def get(self, request: Request, *args, **kwargs):
        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        # фильтруем и отбрасываем дуликаты
        queryset = (ProductInfo.objects.filter(query)
                    .select_related
                    ('shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct())
        serializer = ProductInfoSerializer(queryset, many=True)

        return Response(serializer.data)


class BasketView(APIView):
    """
        Класс для корзины.
    """

    @extend_schema(summary="Получить корзину")
    def get(self, request, *args, **kwargs):
        """ Получить корзину """
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)

        basket = Order.objects.filter(
            user_id=request.user.id, state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F(
                'ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Создание корзины",
        request=OrderSerializer,
        examples=[
            OpenApiExample(
                "Post example",
                description="Test example for the post",
                value={
                    "items": [{"product_info": 1, "quantity": 13},
                              {"product_info": 2, "quantity": 12}],
                },
                # status_codes=[str(status.HTTP_200_OK)],
            ),
        ],
    )
    # создание корзину
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)

        items_sting = request.data.get('items')

        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                return JsonResponse(
                    {'Status': False, 'Errors': 'Неверный формат запроса'})
            else:

                basket, _ = Order.objects.get_or_create(
                    user_id=request.user.id, state='basket')
                objects_created = 0
                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            return JsonResponse(
                                {'Status': False, 'Errors': str(error)})
                        else:
                            objects_created += 1

                    else:

                        return JsonResponse(
                            {'Status': False, 'Errors': serializer.errors})

                return JsonResponse(
                    {'Status': True, 'Создано объектов': objects_created})
        return JsonResponse({'Status': False,
                             'Errors': 'Не указаны все необходимые аргументы'})

    # удалить товары из корзины
    @extend_schema(summary="Удалить товары из корзины")
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)

        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            basket, _ = Order.objects.get_or_create(user_id=request.user.id,
                                                    state='basket')
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()
                return JsonResponse(
                    {'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False,
                             'Errors': 'Не указаны все необходимые аргументы'})

    @extend_schema(
        summary="Добавить позиции в корзину",
        request=OrderSerializer,
        examples=[
            OpenApiExample(
                "Put example",
                description="Test example for the put",
                value={
                    "items": [{"product_info": 9, "quantity": 13},
                              {"product_info": 10, "quantity": 12}],
                },
                # status_codes=[str(status.HTTP_200_OK)],
            ),
        ],
    )
    def put(self, request, *args, **kwargs):
        """
               Update the items in the user's basket.

               Args:
               - request (Request): The Django request object.

               Returns:
               - JsonResponse: The response indicating the status of the operation and any errors.
               """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'},
                                status=403)

        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                return JsonResponse(
                    {'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                basket, _ = Order.objects.get_or_create(
                    user_id=request.user.id, state='basket')
                objects_updated = 0
                for order_item in items_dict:
                    if type(order_item['id']) == int and type(
                            order_item['quantity']) == int:
                        objects_updated += OrderItem.objects.filter(
                            order_id=basket.id, id=order_item['id']).update(
                            quantity=order_item['quantity'])

                return JsonResponse(
                    {'Status': True, 'Обновлено объектов': objects_updated})
        return JsonResponse({'Status': False,
                             'Errors': 'Не указаны все необходимые аргументы'})


class AccountDetails(APIView):
    """
    Класс для управления данными учетной записи пользователя.

    """

    # получить данные
    @extend_schema(
        summary="Получить данные аутентифицированного пользователя.")
    def get(self, request: Request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    # Редактирование методом POST

    @extend_schema(
        summary="Обновить данные учетной записи аутентифицированного пользователя.",
        request=UserSerializer,
        examples=[
            OpenApiExample(
                "Put example",
                description="Test example for the put",
                value=
                {
                    "password": "8490866stas",
                    "email": "ystas2019@mail.ru",
                    "company": "adidadas",
                    "position": "3231113777",
                    "first_name": "Станислав",
                    "last_name": "Юдин"
                },
                # status_codes=[str(status.HTTP_200_OK)],
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)
        # проверяем обязательные аргументы

        if 'password' in request.data:
            errors = {}
            # проверяем пароль на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse(
                    {'Status': False, 'Errors': {'password': error_array}})
            else:
                request.user.set_password(request.data['password'])

        # проверяем остальные данные
        user_serializer = UserSerializer(request.user, data=request.data,
                                         partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse(
                {'Status': False, 'Errors': user_serializer.errors})


class OrderView(APIView):
    """
    Класс для получения и размешения заказов пользователями
   Методы:
     - get: получить сведения о конкретном заказе.
     - сообщение: Создать новый заказ.
     - put: Обновить детали конкретного заказа.
     - удалить: удалить конкретный заказ.
    """

    # получить мои заказы
    @extend_schema(summary="Получение заказов")
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)
        order = (Order.objects.filter(
            user_id=request.user.id).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter')
                 .select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F(
                'ordered_items__product_info__price'))).distinct())

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    # разместить заказ из корзины
    @extend_schema(
        summary="Разместить заказ из корзины",
        request=OrderSerializer,
        examples=[
            OpenApiExample(
                "Post example",
                description="Test example for the post",
                value=
                {
                    "id": "1",
                    "contact": "1",
                },
                # status_codes=[str(status.HTTP_200_OK)],
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)

        if {'id', 'contact'}.issubset(request.data):
            if request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data['id']).update(
                        contact_id=request.data['contact'],
                        state='new')
                except IntegrityError as error:
                    print(error)
                    return JsonResponse({'Status': False,
                                         'Errors': 'Неправильно указаны аргументы'})
                else:
                    if is_updated:
                        new_order.send(sender=self.__class__,
                                       user_id=request.user.id)
                        return JsonResponse({'Status': True})

        return JsonResponse({'Status': False,
                             'Errors': 'Не указаны все необходимые аргументы'})


@extend_schema(summary="Просмотр категорий")
class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# class ShopView(ListAPIView):
#     """
#     Класс для просмотра списка магазинов
#     """
#     queryset = Shop.objects.filter(state=True)
#     serializer_class = ShopSerializer


class PartnerUpdate(APIView):
    """
    Обновление товаров
    """

    @extend_schema(
        summary="Обновление товаров",
        request=ShopSerializer,
        examples=[
            OpenApiExample(
                "Post example",
                description="Test example for the post",
                value={
                    "url": "https://raw.githubusercontent.com/netology-code/pd-diplom/master/data/shop1.yaml",
                },
                # status_codes=[str(status.HTTP_200_OK)],
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'},
                                status=403)

        if request.user.type != 'shop':
            return JsonResponse(
                {'Status': False, 'Error': 'Только для магазинов'}, status=403)
        UserModel = get_user_model()
        user = UserModel.objects.get(pk=request.user.id)
        user_id = user.pk

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:

                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content

                data = load_yaml(stream, Loader=Loader)
                if data == {404: 'Not Found'}:
                    return Response({'message': 'Неверный url'},
                                    status=status.HTTP_404_NOT_FOUND)

                task_product_import.delay(request.user.id, data, user_id,
                                          *args,
                                          **kwargs)

            return JsonResponse({'Status': True})
        return JsonResponse({'Status': False,
                             'Errors': 'Не указаны все необходимые аргументы'})


class PartnerState(APIView):
    """
       Класс для управления состоянием партнера.

        Методы:
        - get: Получить состояние партнера.

    """

    # получить текущий статус
    @extend_schema(summary="Получить текущий статус")
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'},
                                status=403)

        if request.user.type != 'shop':
            return JsonResponse(
                {'Status': False, 'Error': 'Только для магазинов'}, status=403)

        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    # изменить текущий статус
    @extend_schema(
        summary="Изменить текущий статус",
        request=ShopSerializer,
        examples=[
            OpenApiExample(
                "Post example",
                description="Test example for the post",
                value={
                    "state": "on",
                },
                # status_codes=[str(status.HTTP_200_OK)],
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'},
                                status=403)

        if request.user.type != 'shop':
            return JsonResponse(
                {'Status': False, 'Error': 'Только для магазинов'}, status=403)
        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(
                    state=strtobool(state))
                return JsonResponse({'Status': True})
            except ValueError as error:
                return JsonResponse({'Status': False, 'Errors': str(error)})

        return JsonResponse({'Status': False,
                             'Errors': 'Не указаны все необходимые аргументы'})


class Partnerexport(APIView):
    """
    Экспорт товаров в файл
    """

    @extend_schema(summary="Экспорт товаров в файл")
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)
        if request.user.type != 'shop':
            return Response({'message': 'Только для магазинов'},
                            status=status.HTTP_403_FORBIDDEN)

        task_product_export.delay(request.user.id)
        return Response({'status': 'Экспорт данных прошел успешно'},

                        status=status.HTTP_201_CREATED)


class Sentrytest(APIView):
    """Test Sentry вызывает ошибку 'Пользователь» не является итерируемым'"""

    @extend_schema(
        summary="Test Sentry",
        request=ContactSerializer,
        examples=[
            OpenApiExample(
                "Post example",
                description="Test example for the post",
                value=
                {
                    "city": "Gorod",
                    "street": "Shashkin street 40",
                    "house": "Apartament 28",
                    "structure": 123,
                    "building": 123,
                    "apartment": 123,
                    "phone": 89222334847,

                },
                # status_codes=[str(status.HTTP_200_OK)],
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)
        if {'city', 'street', 'phone'}.issubset(request.user):
            # request.data._mutable = True
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response({'status': 'Контакты добавлены'},
                                status=status.HTTP_201_CREATED)
        return Response({'Status': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)


class Updatefile(APIView):

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)
        try:
            file = request.data['file']
        except KeyError:
            raise ParseError('Request has no resource file attached')

        f = User.objects.create_user(avatar_thumbnail=file,id=request.user.id)
        return Response({'status': 'Изображение загружено'},
                        status=status.HTTP_201_CREATED)