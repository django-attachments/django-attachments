#!/usr/bin/env python
import sys
from django.conf import settings
from django.core.management import execute_from_command_line

if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        INSTALLED_APPS=(
            'django.contrib.sessions',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sites',
            'django.contrib.admin',
            'attachments',
            'django_nose',
        ),
        MIDDLEWARE_CLASSES=(
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
        ),
        ROOT_URLCONF='attachments.urls',
        TEST_RUNNER='django_nose.NoseTestSuiteRunner',
        SITE_ID=1,
        MAILER_EMAIL_BACKEND='mailer.tests.TestMailerEmailBackend',
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {
                    # ... some options here ...
                },
            },
        ],
    )


def runtests():
    argv = sys.argv[:1] + ['test', 'attachments', '--traceback'] + sys.argv[1:]  # noqa
    execute_from_command_line(argv)


if __name__ == '__main__':
    runtests()
