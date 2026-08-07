from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models


iran_mobile_validator = RegexValidator(
    regex=r"^09\d{9}$",
    message="شماره موبایل باید با 09 شروع شود و 11 رقم باشد.",
)


class UserManager(BaseUserManager):
    def create_user(self, mobile, password=None, **extra_fields):
        if not mobile:
            raise ValueError("Mobile number is required")

        mobile = mobile.strip()

        user = self.model(
            mobile=mobile,
            **extra_fields,
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            mobile=mobile,
            password=password,
            **extra_fields,
        )


class User(AbstractUser):
    username = None

    mobile = models.CharField(
        max_length=11,
        unique=True,
        validators=[iran_mobile_validator],
        verbose_name="شماره موبایل",
    )

    is_mobile_verified = models.BooleanField(
        default=False,
        verbose_name="تأیید شماره موبایل",
    )

    USERNAME_FIELD = "mobile"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.mobile

class OTPCode(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="otp_codes",
        db_index=True,
        verbose_name="کاربر",
    )

    code = models.CharField(
        max_length=6,
        db_index=True,
        verbose_name="کد تأیید",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ایجاد",
    )

    expires_at = models.DateTimeField(
        verbose_name="زمان انقضا",
    )

    attempts = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="تعداد تلاش",
    )

    is_used = models.BooleanField(
        default=False,
        verbose_name="استفاده شده",
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.user.mobile} - {self.code}"