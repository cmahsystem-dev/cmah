from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, mobile, password=None, **extra_fields):
        if not mobile:
            raise ValueError("Mobile number is required")

        user = self.model(mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(mobile, password, **extra_fields)


class User(AbstractUser):
    username = None

    mobile = models.CharField(
        max_length=11,
        unique=True,
        verbose_name="شماره موبایل"
    )

    is_mobile_verified = models.BooleanField(
        default=False,
        verbose_name="تأیید شماره موبایل"
    )

    USERNAME_FIELD = "mobile"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.mobile