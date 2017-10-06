#!/usr/bin/python3

from os import execlp
from os.path import exists


def main():
    if not exists('db.sqlite3'):
        from os import system, environ
        from django.contrib.auth.models import User
        system('python3 manage.py collectstatic')
        system('python3 manage.py migrate')
        User.objects.create_superuser(environ.get('ROOT_USERNAME', 'root'),
                                      environ.get('ROOT_EMAIL', None),
                                      environ.get('ROOT_PASSWORD', None))
    execlp('python3', 'manage.py', 'runserver', '0:80')

if __name__ == '__main__':
    main()
