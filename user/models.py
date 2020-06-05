from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager


class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    is_gm = models.BooleanField(default=False)

    member_point = models.PositiveIntegerField(default=0)

    USERNAME_FIELD = 'email'

    objects = BaseUserManager()
