FROM python:3
EXPOSE 80
VOLUME /static

WORKDIR /hackergame

RUN pip install --no-cache-dir django
COPY . .
ENV DEBUG=false
RUN python manage.py collectstatic --noinput

CMD python manage.py runserver 0:80
