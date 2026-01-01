from django.db import models
from django.contrib.auth import get_user_model
import random

User = get_user_model()

def generate_customer_id():
    """Generate a unique 5-digit customer ID"""
    while True:
        customer_id = str(random.randint(10000, 99999))
        if not Account.objects.filter(customer_id=customer_id).exists():
            return customer_id

def generate_account_number():
    """Generate a unique 10-digit account number"""
    while True:
        account_number = str(random.randint(1000000000, 9999999999))
        if not Account.objects.filter(account_number=account_number).exists():
            return account_number

class Account(models.Model):
    """
    Bank Account model
    One-to-one relationship with User
    """
    ACCOUNT_STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Frozen', 'Frozen'),
    ]
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='account'
    )
    customer_id = models.CharField(
        max_length=5,
        unique=True,
        default=generate_customer_id,
        help_text="5-digit unique customer ID"
    )
    account_number = models.CharField(
        max_length=10,
        unique=True,
        default=generate_account_number,
        help_text="10-digit unique account number"
    )
    ifsc_code = models.CharField(
        max_length=11,
        default='NEOBANKX',
        help_text="IFSC code for the bank"
    )
    account_holder_name = models.CharField(
        max_length=255,
        help_text="Full name of account holder"
    )
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        help_text="Contact phone number"
    )
    phone_verified = models.BooleanField(
        default=False,
        help_text="Whether phone number is verified"
    )
    phone_verification_code = models.CharField(
        max_length=6,
        null=True,
        blank=True,
        help_text="Verification code for phone"
    )
    phone_verification_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When verification code was sent"
    )
    pan_number = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        help_text="PAN Card Number"
    )
    aadhar_number = models.CharField(
        max_length=12,
        unique=True,
        null=True,
        blank=True,
        help_text="Aadhar Card Number"
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="Date of Birth"
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
        help_text="Gender"
    )
    address = models.TextField(
        null=True,
        blank=True,
        help_text="Full residential address"
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Current account balance"
    )
    account_status = models.CharField(
        max_length=10,
        choices=ACCOUNT_STATUS_CHOICES,
        default='Active',
        help_text="Current status of the account"
    )
    opened_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Date when account was opened"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last updated timestamp"
    )
    
    def __str__(self):
        return f"{self.account_holder_name} - {self.account_number}"
    
    class Meta:
        verbose_name = 'Bank Account'
        verbose_name_plural = 'Bank Accounts'
        ordering = ['-opened_date']
