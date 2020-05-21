from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser


class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=20, unique=True)
    is_gm = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
