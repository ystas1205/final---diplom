FROM python:latest
WORKDIR /app

COPY . /app
COPY ./requirements.txt .
#RUN apt-get update && apt-get install -y curl && apt-get clean
RUN pip install -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#ENTRYPOINT ["/app/entrypoint.sh"]
CMD python manage.py migrate \
     && pip install --upgrade pip \
     && python manage.py collectstatic --no-input \
     && gunicorn product_service.wsgi:application --bind 0.0.0.0:8000




#    && python manage.py collectstatic --no-input \

#    && gunicorn prediction.wsgi:application --bind 0.0.0.0:8000 --log-level info
