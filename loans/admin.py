from django.contrib import admin
from .models import Loan, EMIPayment

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """
    Admin interface for Loan model
    """
    list_display = ('id', 'account', 'loan_type', 'loan_amount', 'interest_rate', 'tenure_months', 'loan_status', 'application_date')
    list_filter = ('loan_type', 'loan_status', 'application_date')
    search_fields = ('account__account_holder_name', 'account__account_number', 'purpose')
    readonly_fields = ('application_date', 'monthly_emi', 'disbursement_date', 'closure_date')
    date_hierarchy = 'application_date'
    
    fieldsets = (
        ('Loan Information', {
            'fields': ('account', 'loan_type', 'loan_amount', 'interest_rate', 'tenure_months')
        }),
        ('EMI Details', {
            'fields': ('monthly_emi', 'remaining_balance', 'next_emi_date', 'autopay_enabled')
        }),
        ('Status', {
            'fields': ('loan_status', 'application_date', 'approval_date', 'disbursement_date', 'closure_date')
        }),
        ('Additional Information', {
            'fields': ('purpose',)
        }),
    )
    
    actions = ['approve_loans', 'reject_loans', 'disburse_loans']
    
    def approve_loans(self, request, queryset):
        """Approve selected loans"""
        from django.utils import timezone
        updated = queryset.filter(loan_status='Pending').update(
            loan_status='Approved',
            approval_date=timezone.now()
        )
        self.message_user(request, f'{updated} loan(s) have been approved.')
    approve_loans.short_description = 'Approve selected loans'
    
    def reject_loans(self, request, queryset):
        """Reject selected loans"""
        updated = queryset.filter(loan_status='Pending').update(loan_status='Rejected')
        self.message_user(request, f'{updated} loan(s) have been rejected.')
    reject_loans.short_description = 'Reject selected loans'
    
    def disburse_loans(self, request, queryset):
        """Disburse selected approved loans and credit amount to accounts"""
        from django.db import transaction as db_transaction
        from transactions.models import Transaction
        from django.utils import timezone
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta
        
        disbursed_count = 0
        
        for loan in queryset.filter(loan_status='Approved'):
            with db_transaction.atomic():
                # Credit the loan amount to the user's account
                account = loan.account
                account.balance += loan.loan_amount
                account.save()
                
                # Create a transaction record
                Transaction.objects.create(
                    from_account=None,  # No source account for loan disbursement
                    to_account=account,
                    amount=loan.loan_amount,
                    transaction_type='Deposit',
                    status='Success',
                    description=f'Loan disbursed - {loan.loan_type} Loan (ID: {loan.id})',
                    balance_after=account.balance,
                    account=account
                )
                
                # Update loan status and details
                now = timezone.now()
                loan.loan_status = 'Disbursed'
                loan.disbursement_date = now
                loan.remaining_balance = loan.monthly_emi * loan.tenure_months  # Total payable
                loan.next_emi_date = (now + relativedelta(months=1)).date()
                loan.save()
                
                # Create EMI schedule
                emi_date = loan.next_emi_date
                for emi_num in range(1, loan.tenure_months + 1):
                    EMIPayment.objects.create(
                        loan=loan,
                        emi_number=emi_num,
                        due_date=emi_date,
                        emi_amount=loan.monthly_emi,
                        payment_status='Pending'
                    )
                    emi_date = emi_date + relativedelta(months=1)
                
                disbursed_count += 1
        
        self.message_user(request, f'{disbursed_count} loan(s) have been disbursed, credited to accounts, and EMI schedules created.')
    disburse_loans.short_description = 'Disburse selected approved loans'


@admin.register(EMIPayment)
class EMIPaymentAdmin(admin.ModelAdmin):
    """
    Admin interface for EMI Payment model
    """
    list_display = ('id', 'loan', 'emi_number', 'due_date', 'emi_amount', 'paid_amount', 'payment_status', 'payment_method', 'payment_date')
    list_filter = ('payment_status', 'payment_method', 'due_date')
    search_fields = ('loan__account__account_holder_name', 'transaction_reference')
    readonly_fields = ('payment_date',)
    date_hierarchy = 'due_date'
