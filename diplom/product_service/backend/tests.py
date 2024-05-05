

from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from backend.models import User, ConfirmEmailToken, Contact


class UserTests(APITestCase):
    def setUp(self):

        # данные для тестирование пользователя
        self.data_user = {
            "email": "test_email@mail.ru",
            "password": "password1234567890",
            "company": "company_name",
            "position": 211233,
            "first_name": "first_name",
            "last_name": "last_name",

        }
        # данные для тестирование пользователя c невалидной почтой
        self.invalid_mail_user = {
            "email": "email",
            "password": "password1234567890",
            "company": "company_name",
            "position": 211233,
            "first_name": "first_name",
            "last_name": "last_name",

        }
        # создание пользователя для получения токена подтверждения
        self.user_test = User.objects.create_user(email="test_email",
                                                  password="password",
                                                  )
        self.user_test.save()

        # получение токена для подтверждения
        self.user_conf_token = ConfirmEmailToken.objects.create(
            user=self.user_test)
        if self.user_conf_token:
            self.user_conf_token.user.is_active = True
            self.user_conf_token.user.save()
        # получение токена
        if self.user_test is not None:
            if self.user_test.is_active:
                self.user_token, _ = Token.objects.get_or_create(
                    user=self.user_test)
                self.user_token.save()

        # данные для тестирование пользователя
        self.data_contact = {
            "user_id": self.user_test.id,
            "id": '1',
            "city": 'city1',
            "street": 'street1',
            "house": 'house1',
            "structure": 'structure1',
            "building": 'building1',
            "apartment": 'apartment1',
            "phone": 'phone1'}

    def test_create_user(self):
        """ Тест регестрации пользователя """
        url = reverse('backend:user-register')
        response = self.client.post(url, self.data_user, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_email(self):
        """ Тест регестрации пользователя c невалидной почтой """
        url = reverse('backend:user-register')
        response = self.client.post(url, self.invalid_mail_user, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'Status': False, 'Errors': {
            'email': ['Введите правильный адрес электронной почты.']}})
        print(response.json())

    def test_argument_validation(self):
        """ Тест на введение не полных данных пользователя """
        url = reverse('backend:user-register')
        response = self.client.post(url, data={"password": "password",
                                               "company": "company_name"},
                                    format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(),
                         {'status': 'Не указаны все необходимые аргументы'}
                         )

    def test_mailing_address_confirmation(self):
        """ Тест подтверждение почты  пользователя """
        url = reverse('backend:user-register-confirm')
        response = self.client.post(url, data={"email": self.user_test.email,
                                               "token": self.user_conf_token.key},
                                    format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(),
                         {'status': 'Почтовый адрес подтвержден'}
                         )


class ContactTests(UserTests):

    def test_get_user(self):
        """ Тест на получение контактных данных пользователя """
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user_token.key)
        contact = Contact.objects.create(user_id=self.user_test.id,
                                         city='city',
                                         street='street', house='house',
                                         structure='structure',
                                         building='building',
                                         apartment='apartment',
                                         phone='phone')
        url = reverse('backend:user-contact')
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_user_contact(self):
        """ Тест на создание контактных данных пользователя """
        count = Contact.objects.count()
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user_token.key)
        url = reverse('backend:user-contact')
        response = self.client.post(url, self.data_contact, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contact.objects.count(), count + 1)

    def test_update_user_contact(self):
        """ Тест на обновление контактных данных пользователя """
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user_token.key)
        url = reverse('backend:user-contact')
        contact = Contact.objects.create(user_id=self.user_test.id,
                                         id="1",
                                         city='city',
                                         street='street', house='house',
                                         structure='structure',
                                         building='building',
                                         apartment='apartment',
                                         phone='phone')
        response = self.client.put(url, self.data_contact,
                                   format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'status': 'Контакты обновлены'})

    def test_delete_user_contact(self):
        """ Тест на удаление контактных данных пользователя """
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user_token.key)
        url = reverse('backend:user-contact')
        contact = Contact.objects.create(user_id=self.user_test.id,
                                         id="1",
                                         city='city',
                                         street='street', house='house',
                                         structure='structure',
                                         building='building',
                                         apartment='apartment',
                                         phone='phone')
        count_contact = Contact.objects.count()
        response = self.client.delete(url, data={"items": "1"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Contact.objects.count(), count_contact - 1)
        self.assertEqual(response.data,
                         {'message': f'Удалено {count_contact}'})
