from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Adds phone_number and account creation tracking.
    """
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        help_text="User's phone number for transfers"
    )
    is_account_created = models.BooleanField(
        default=False,
        help_text="Whether user has created a bank account"
    )
    
    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
