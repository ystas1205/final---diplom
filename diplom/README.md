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