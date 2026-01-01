from django.db import models
from banking.models import Account

class Loan(models.Model):
    """
    Loan model for tracking loan applications
    """
    LOAN_TYPE_CHOICES = [
        ('Personal', 'Personal Loan'),
        ('Home', 'Home Loan'),
        ('Auto', 'Auto Loan'),
        ('Education', 'Education Loan'),
    ]
    
    LOAN_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Disbursed', 'Disbursed'),
        ('Closed', 'Closed'),
    ]
    
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='loans',
        help_text="Account for which loan is applied"
    )
    loan_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Requested loan amount"
    )
    loan_type = models.CharField(
        max_length=10,
        choices=LOAN_TYPE_CHOICES,
        help_text="Type of loan"
    )
    loan_status = models.CharField(
        max_length=10,
        choices=LOAN_STATUS_CHOICES,
        default='Pending',
        help_text="Current loan status"
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Annual interest rate (%)"
    )
    tenure_months = models.IntegerField(
        help_text="Loan tenure in months"
    )
    monthly_emi = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monthly EMI amount"
    )
    purpose = models.TextField(
        blank=True,
        help_text="Purpose of the loan"
    )
    application_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Date when loan was applied"
    )
    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when loan was approved"
    )
    disbursement_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when loan was disbursed"
    )
    remaining_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Remaining loan amount to be paid"
    )
    autopay_enabled = models.BooleanField(
        default=False,
        help_text="Auto-deduct EMI from account balance"
    )
    next_emi_date = models.DateField(
        null=True,
        blank=True,
        help_text="Next EMI due date"
    )
    closure_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when loan was closed"
    )
    
    def __str__(self):
        return f"{self.loan_type} - {self.loan_amount} - {self.account.account_holder_name}"
    
    @property
    def is_active(self):
        """Check if loan is active (disbursed but not closed)"""
        return self.loan_status == 'Disbursed'
    
    @property
    def total_amount_payable(self):
        """Calculate total amount to be paid including interest"""
        if self.monthly_emi and self.tenure_months:
            return float(self.monthly_emi) * self.tenure_months
        return float(self.loan_amount)
    
    @property
    def total_interest(self):
        """Calculate total interest to be paid"""
        return self.total_amount_payable - float(self.loan_amount)
    
    @property
    def paid_emis_count(self):
        """Count number of EMIs paid"""
        return self.emi_payments.filter(payment_status='Paid').count()
    
    @property
    def pending_emis_count(self):
        """Count number of EMIs pending"""
        return self.tenure_months - self.paid_emis_count
    
    def calculate_emi(self):
        """
        Calculate monthly EMI using the formula:
        EMI = [P x R x (1+R)^N] / [(1+R)^N-1]
        where P = loan amount, R = monthly rate, N = tenure in months
        """
        if self.loan_amount and self.interest_rate and self.tenure_months:
            p = float(self.loan_amount)
            r = float(self.interest_rate) / (12 * 100)  # Monthly rate
            n = self.tenure_months
            
            if r > 0:
                emi = (p * r * pow(1 + r, n)) / (pow(1 + r, n) - 1)
            else:
                emi = p / n
            
            return round(emi, 2)
        return 0
    
    def save(self, *args, **kwargs):
        """Override save to calculate EMI"""
        if not self.monthly_emi:
            self.monthly_emi = self.calculate_emi()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Loan'
        verbose_name_plural = 'Loans'
        ordering = ['-application_date']


class EMIPayment(models.Model):
    """
    Model to track individual EMI payments
    """
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue'),
        ('Failed', 'Failed'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('Auto', 'Auto-Pay'),
        ('Manual', 'Manual Payment'),
        ('Preclosure', 'Loan Preclosure'),
    ]
    
    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='emi_payments',
        help_text="Associated loan"
    )
    emi_number = models.IntegerField(
        help_text="EMI sequence number (1, 2, 3...)"
    )
    due_date = models.DateField(
        help_text="EMI due date"
    )
    emi_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="EMI amount"
    )
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Amount paid"
    )
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when EMI was paid"
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='Pending',
        help_text="Payment status"
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        null=True,
        blank=True,
        help_text="Payment method"
    )
    transaction_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Transaction reference number"
    )
    
    def __str__(self):
        return f"EMI #{self.emi_number} - {self.loan.loan_type} - {self.payment_status}"
    
    class Meta:
        verbose_name = 'EMI Payment'
        verbose_name_plural = 'EMI Payments'
        ordering = ['loan', 'emi_number']
        unique_together = ['loan', 'emi_number']
