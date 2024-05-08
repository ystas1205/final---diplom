# Дипломная работа к профессии Python-разработчик «API Сервис заказа товаров для розничных сетей».

#### Запускаем docker-compose.yaml командой docker compose up и запускаем в браузере 127.0.0.1/api/v1




##### Переменные для redis

###### CELERY_BROKER_URL ='redis://redis:6379/0'
###### CELERY_RESULT_BACKEND = 'redis://redis:6379/1'

##### Согласно документации social oauth2 Чтобы взаимодействовать с вашим API и отправлять запросы,
##### вы можете использовать редактор Swagger. Следующие команды позволят вам запустить
##### редактор Swagger и начать взаимодействовать с вашим API.

#### но это не работает
docker run --rm -p 8080:8080 -v $(pwd):/tmp -e SWAGGER_FILE=/tmp/api.yaml swaggerapi/swagger-editor

#### Тестирование авторизации  через социальную сеть в контакте http://127.0.0.1/auth/convert-token

#### grant_type        convert_token
#### client_id         8LhRSSvXLtSNQP23VTwNFUAZgiKgCLe86XcUSozn
#### backend           vk-oauth2
#### token             vk1.a.dsvx8u8my-DtVPFrpjHsoeggkSVeozE4Kf2hKgXGOrE6kdER959
####                     KE41ceu581NX3t3msg8DpHEekBxQzQxnhlzWwJq3iH_5YNGbv7r_iPdV1U
####                     J0XYVfw66IHYkSatVXNorY6Jjztfn6F9uFEF1YEVxo3HLRpDeWKjiSwQyim
####                     KAhN1Ds7yTnkj0-z5-O4jlm8JDDMqpcihJatFLlmsN114w 


#### токен для запроса генерируется по ссылке
#### https://login.vk.com/?act=openapi&oauth=1&aid=51664963&location=127.0.0.1&new=1&response_type=code