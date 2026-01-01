from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def index(request):
    """
    Landing page view - shows information about ASTRALFIN
    """
    return render(request, 'core/index.html')

@login_required
def dashboard(request):
    """
    Dashboard view for logged-in users
    Shows account summary and quick actions
    """
    context = {
        'user': request.user,
    }
    
    # If user has an account, get account details and statistics
    if hasattr(request.user, 'account'):
        from transactions.models import Transaction
        from loans.models import Loan
        from investments.models import Investment
        from django.db.models import Sum, Count
        
        account = request.user.account
        context['account'] = account
        
        # Dashboard statistics
        context['total_transactions'] = Transaction.objects.filter(account=account).count()
        context['active_loans'] = Loan.objects.filter(
            account=account, 
            loan_status='Disbursed'
        ).count()
        
        # Investment portfolio value
        investment_data = Investment.objects.filter(
            account=account,
            investment_status='Active'
        ).aggregate(
            total_value=Sum('current_value'),
            count=Count('id')
        )
        context['investment_value'] = investment_data['total_value'] or 0
        context['investment_count'] = investment_data['count'] or 0
        
        # Recent transactions (last 5)
        context['recent_transactions'] = Transaction.objects.filter(
            account=account
        ).order_by('-timestamp')[:5]
    
    return render(request, 'core/dashboard.html', context)
