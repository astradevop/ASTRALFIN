from django.db import models
from banking.models import Account
from django.utils import timezone

class Investment(models.Model):
    """
    Investment model for tracking user investments
    """
    INVESTMENT_TYPE_CHOICES = [
        ('Mutual_Fund', 'Mutual Fund'),
        ('Stocks', 'Stocks'),
        ('Bonds', 'Bonds'),
        ('Fixed_Deposit', 'Fixed Deposit'),
        ('SIP', 'Systematic Investment Plan'),
    ]
    
    INVESTMENT_STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Matured', 'Matured'),
        ('Closed', 'Closed'),
        ('Pending', 'Pending'),
    ]
    
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='investments',
        help_text="Account from which investment is made"
    )
    investment_type = models.CharField(
        max_length=20,
        choices=INVESTMENT_TYPE_CHOICES,
        help_text="Type of investment"
    )
    investment_name = models.CharField(
        max_length=200,
        help_text="Name of the investment (e.g., HDFC Balanced Fund)"
    )
    principal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Initial investment amount"
    )
    current_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Current market value"
    )
    expected_return_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Expected annual return rate (%)"
    )
    investment_status = models.CharField(
        max_length=10,
        choices=INVESTMENT_STATUS_CHOICES,
        default='Active',
        help_text="Current investment status"
    )
    start_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Investment start date"
    )
    maturity_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected maturity date"
    )
    risk_level = models.CharField(
        max_length=20,
        choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')],
        default='Medium',
        help_text="Risk level of investment"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )
    
    def __str__(self):
        return f"{self.investment_name} - ₹{self.principal_amount}"
    
    @property
    def profit_loss(self):
        """Calculate profit or loss"""
        return float(self.current_value) - float(self.principal_amount)
    
    @property
    def return_percentage(self):
        """Calculate return percentage"""
        if self.principal_amount > 0:
            return (self.profit_loss / float(self.principal_amount)) * 100
        return 0
    
    @property
    def is_profitable(self):
        """Check if investment is profitable"""
        return self.current_value > self.principal_amount
    
    class Meta:
        verbose_name = 'Investment'
        verbose_name_plural = 'Investments'
        ordering = ['-start_date']


class InvestmentTransaction(models.Model):
    """
    Model to track investment buy/sell transactions
    """
    TRANSACTION_TYPE_CHOICES = [
        ('Buy', 'Buy'),
        ('Sell', 'Sell'),
        ('Dividend', 'Dividend'),
    ]
    
    investment = models.ForeignKey(
        Investment,
        on_delete=models.CASCADE,
        related_name='transactions',
        help_text="Associated investment"
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Type of transaction"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Transaction amount"
    )
    units = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Number of units bought/sold"
    )
    price_per_unit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price per unit"
    )
    transaction_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Transaction date"
    )
    reference_number = models.CharField(
        max_length=100,
        unique=True,
        help_text="Transaction reference"
    )
    
    def __str__(self):
        return f"{self.transaction_type} - {self.investment.investment_name} - ₹{self.amount}"
    
    class Meta:
        verbose_name = 'Investment Transaction'
        verbose_name_plural = 'Investment Transactions'
        ordering = ['-transaction_date']
