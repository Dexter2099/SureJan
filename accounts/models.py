from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(max_length=191, unique=True)

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
