from django.contrib.auth import get_user_model
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
    Для регистрации покупателей
    """

    # Регистрация методом POST

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

    # Регистрация методом POST
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
                return Response({'status': 'Почтовый адрес подтвержден '},
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
    Класс для получения удаление добавление и зменение контактных данных
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)
        contact = Contact.objects.filter(user=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

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


class ShopView(APIView):
    """
    Класс для получения списка магазинов
    """

    def get(self, request, *args, **kwargs):
        shop = Shop.objects.filter(state=True)
        serializer = ShopSerializer(shop, many=True)
        return Response(serializer.data)


class ProductInfoView(APIView):
    """
    Класс для поиска товаров.
    """

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
    # получить корзину
    def get(self, request, *args, **kwargs):
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

    # редактировать корзину
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

    # добавить позиции в корзину
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
    A class for managing user account details.

    Methods:
    - get: Retrieve the details of the authenticated user.
    - post: Update the account details of the authenticated user.

    Attributes:
    - None
    """

    # получить данные
    def get(self, request: Request, *args, **kwargs):
        """
               Retrieve the details of the authenticated user.

               Args:
               - request (Request): The Django request object.

               Returns:
               - Response: The response containing the details of the authenticated user.
        """
        if not request.user.is_authenticated:
            return Response({'message': 'Требуется войти'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    # Редактирование методом POST
    def post(self, request, *args, **kwargs):
        """
                Update the account details of the authenticated user.

                Args:
                - request (Request): The Django request object.

                Returns:
                - JsonResponse: The response indicating the status of the operation and any errors.
                """
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
                a = request.user

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
    Methods:
    - get: Retrieve the details of a specific order.
    - post: Create a new order.
    - put: Update the details of a specific order.
    - delete: Delete a specific order.

    Attributes:
    - None
    """

    # получить мои заказы
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


class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    Класс для просмотра списка магазинов
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class PartnerUpdate(APIView):
    """
    Обновление товаров
    """

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
       A class for managing partner state.

       Methods:
       - get: Retrieve the state of the partner.

       Attributes:
       - None
       """

    # получить текущий статус
    def get(self, request, *args, **kwargs):
        """
               Retrieve the state of the partner.

               Args:
               - request (Request): The Django request object.

               Returns:
               - Response: The response containing the state of the partner.
               """
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
    def post(self, request, *args, **kwargs):
        """
               Update the state of a partner.

               Args:
               - request (Request): The Django request object.

               Returns:
               - JsonResponse: The response indicating the status of the operation and any errors.
               """
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

