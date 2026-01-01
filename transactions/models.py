from django.db import models
from banking.models import Account
import uuid

class Transaction(models.Model):
    """
    Transaction model for tracking all money movements
    """
    TRANSACTION_TYPE_CHOICES = [
        ('Deposit', 'Deposit'),
        ('Transfer', 'Transfer'),
        ('Withdrawal', 'Withdrawal'),
    ]
    
    STATUS_CHOICES = [
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Pending', 'Pending'),
    ]
    
    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Unique transaction ID"
    )
    from_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='outgoing_transactions',
        help_text="Source account (null for deposits)"
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='incoming_transactions',
        help_text="Destination account (null for withdrawals/EMI payments)"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Transaction amount"
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Type of transaction"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Success',
        help_text="Transaction status"
    )
    description = models.TextField(
        blank=True,
        help_text="Transaction description or note"
    )
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Account balance after this transaction"
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions_ledger',
        help_text="Account whose ledger this transaction belongs to"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Transaction timestamp"
    )
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-timestamp']
