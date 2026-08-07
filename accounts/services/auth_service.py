from django.contrib.auth import (
    login as django_login,
    logout as django_logout,
)
from django.http import HttpRequest

from accounts.models import User


class AuthService:

    @staticmethod
    def login(request: HttpRequest, user: User) -> None:
        django_login(request, user)

    @staticmethod
    def logout(request: HttpRequest) -> None:
        django_logout(request)