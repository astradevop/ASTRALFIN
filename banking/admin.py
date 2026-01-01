from django.contrib import admin
from .models import Account

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """
    Admin interface for Account model
    """
    list_display = ('account_number', 'account_holder_name', 'customer_id', 'balance', 'account_status', 'opened_date')
    list_filter = ('account_status', 'opened_date')
    search_fields = ('account_number', 'customer_id', 'account_holder_name', 'user__username', 'user__email')
    readonly_fields = ('customer_id', 'account_number', 'opened_date', 'updated_at')
    
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'account_holder_name', 'customer_id', 'account_number', 'ifsc_code')
        }),
        ('Financial Information', {
            'fields': ('balance', 'account_status')
        }),
        ('Timestamps', {
            'fields': ('opened_date', 'updated_at')
        }),
    )
