from django.contrib import admin
from .models import Investment, InvestmentTransaction

@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    """
    Admin interface for Investment model
    """
    list_display = ('id', 'investment_name', 'investment_type', 'principal_amount', 
                    'current_value', 'profit_loss_display', 'investment_status', 'start_date')
    list_filter = ('investment_type', 'investment_status', 'risk_level', 'start_date')
    search_fields = ('investment_name', 'account__account_holder_name')
    readonly_fields = ('start_date', 'profit_loss', 'return_percentage')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Investment Information', {
            'fields': ('account', 'investment_type', 'investment_name', 'risk_level')
        }),
        ('Financial Details', {
            'fields': ('principal_amount', 'current_value', 'expected_return_rate', 
                      'profit_loss', 'return_percentage')
        }),
        ('Dates', {
            'fields': ('start_date', 'maturity_date')
        }),
        ('Status', {
            'fields': ('investment_status', 'notes')
        }),
    )
    
    def profit_loss_display(self, obj):
        profit = obj.profit_loss
        return f"₹{profit:,.2f}" if profit >= 0 else f"-₹{abs(profit):,.2f}"
    profit_loss_display.short_description = 'Profit/Loss'


@admin.register(InvestmentTransaction)
class InvestmentTransactionAdmin(admin.ModelAdmin):
    """
    Admin interface for Investment Transaction model
    """
    list_display = ('id', 'investment', 'transaction_type', 'amount', 
                    'reference_number', 'transaction_date')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('reference_number', 'investment__investment_name')
    readonly_fields = ('transaction_date',)
    date_hierarchy = 'transaction_date'
