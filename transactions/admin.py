from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin interface for Transaction model
    """
    list_display = ('transaction_id', 'transaction_type', 'amount', 'from_account', 'to_account', 'status', 'timestamp')
    list_filter = ('transaction_type', 'status', 'timestamp')
    search_fields = ('transaction_id', 'from_account__account_number', 'to_account__account_number', 'description')
    readonly_fields = ('transaction_id', 'timestamp')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'transaction_type', 'amount', 'status')
        }),
        ('Account Information', {
            'fields': ('from_account', 'to_account')
        }),
        ('Additional Details', {
            'fields': ('description', 'timestamp')
        }),
    )
