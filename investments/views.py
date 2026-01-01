from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction as db_transaction
from django.db.models import Sum, Q
from django.utils import timezone
from .models import Investment, InvestmentTransaction
from .forms import InvestmentForm, WithdrawInvestmentForm
from transactions.models import Transaction
import uuid

@login_required
def investment_dashboard(request):
    """
    Investment dashboard showing summary
    """
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    investments = Investment.objects.filter(account=request.user.account)
    
    # Calculate totals
    total_invested = investments.aggregate(
        total=Sum('principal_amount')
    )['total'] or 0
    
    total_current_value = investments.aggregate(
        total=Sum('current_value')
    )['total'] or 0
    
    total_profit_loss = float(total_current_value) - float(total_invested)
    
    active_count = investments.filter(investment_status='Active').count()
    
    context = {
        'investments': investments[:5],  # Latest 5
        'total_invested': total_invested,
        'total_current_value': total_current_value,
        'total_profit_loss': total_profit_loss,
        'active_count': active_count,
    }
    
    return render(request, 'investments/investment_dashboard.html', context)


@login_required
def create_investment(request):
    """
    View to create a new investment
    """
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    account = request.user.account
    
    if request.method == 'POST':
        form = InvestmentForm(request.POST)
        if form.is_valid():
            investment = form.save(commit=False)
            investment.account = account
            investment.current_value = investment.principal_amount  # Initial value
            
            # Check if user has sufficient balance
            if account.balance < investment.principal_amount:
                messages.error(request, f'Insufficient balance. Required: ₹{investment.principal_amount}, Available: ₹{account.balance}')
                return render(request, 'investments/create_investment.html', {'form': form, 'account_balance': account.balance})
            
            with db_transaction.atomic():
                # Deduct from account
                account.balance -= investment.principal_amount
                account.save()
                
                # Save investment
                investment.save()
                
                # Create transaction record
                Transaction.objects.create(
                    from_account=account,
                    to_account=None,
                    amount=investment.principal_amount,
                    transaction_type='Withdrawal',
                    status='Success',
                    description=f'Investment in {investment.investment_name}',
                    balance_after=account.balance,
                    account=account
                )
                
                # Create investment transaction
                InvestmentTransaction.objects.create(
                    investment=investment,
                    transaction_type='Buy',
                    amount=investment.principal_amount,
                    reference_number=f'INV-{uuid.uuid4().hex[:8].upper()}'
                )
                
                messages.success(request, f'✅ Investment of ₹{investment.principal_amount} created successfully!')
                return redirect('investments:investment_dashboard')
    else:
        form = InvestmentForm()
    
    return render(request, 'investments/create_investment.html', {
        'form': form,
        'account_balance': account.balance
    })


@login_required
def portfolio_view(request):
    """
    View all investments (portfolio)
    """
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    investments = Investment.objects.filter(account=request.user.account)
    
    # Summary statistics
    total_invested = sum(float(inv.principal_amount) for inv in investments)
    total_current = sum(float(inv.current_value) for inv in investments)
    total_profit = total_current - total_invested
    
    context = {
        'investments': investments,
        'total_invested': total_invested,
        'total_current': total_current,
        'total_profit': total_profit,
    }
    
    return render(request, 'investments/portfolio_view.html', context)


@login_required
def investment_details(request, investment_id):
    """
    View details of a specific investment
    """
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    investment = get_object_or_404(
        Investment, 
        id=investment_id, 
        account=request.user.account
    )
    
    # Get transaction history
    transactions = investment.transactions.all()
    
    context = {
        'investment': investment,
        'transactions': transactions,
    }
    
    return render(request, 'investments/investment_details.html', context)


@login_required
def withdraw_investment(request, investment_id):
    """
    Withdraw/close an investment
    """
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    investment = get_object_or_404(
        Investment, 
        id=investment_id, 
        account=request.user.account
    )
    
    if investment.investment_status == 'Closed':
        messages.error(request, 'This investment is already closed.')
        return redirect('investments:investment_details', investment_id=investment.id)
    
    account = request.user.account
    
    if request.method == 'POST':
        form = WithdrawInvestmentForm(request.POST)
        if form.is_valid():
            withdrawal_amount = form.cleaned_data['withdrawal_amount']
            
            if withdrawal_amount > investment.current_value:
                messages.error(request, f'Withdrawal amount cannot exceed current value: ₹{investment.current_value}')
                return render(request, 'investments/withdraw_investment.html', {
                    'form': form,
                    'investment': investment,
                    'account_balance': account.balance
                })
            
            with db_transaction.atomic():
                # Credit to account
                account.balance += withdrawal_amount
                account.save()
                
                # Update investment
                investment.current_value -= withdrawal_amount
                if investment.current_value <= 0:
                    investment.investment_status = 'Closed'
                investment.save()
                
                # Create transaction record
                Transaction.objects.create(
                    from_account=None,
                    to_account=account,
                    amount=withdrawal_amount,
                    transaction_type='Deposit',
                    status='Success',
                    description=f'Withdrawal from {investment.investment_name}',
                    balance_after=account.balance,
                    account=account
                )
                
                # Create investment transaction
                InvestmentTransaction.objects.create(
                    investment=investment,
                    transaction_type='Sell',
                    amount=withdrawal_amount,
                    reference_number=f'WDR-{uuid.uuid4().hex[:8].upper()}'
                )
                
                messages.success(request, f'✅ Withdrawal of ₹{withdrawal_amount} successful!')
                return redirect('investments:investment_details', investment_id=investment.id)
    else:
        form = WithdrawInvestmentForm()
    
    context = {
        'form': form,
        'investment': investment,
        'account_balance': account.balance,
    }
    
    return render(request, 'investments/withdraw_investment.html', context)


@login_required
def update_investment_value(request, investment_id):
    """
    Update current market value of investment (admin feature)
    """
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    investment = get_object_or_404(
        Investment, 
        id=investment_id, 
        account=request.user.account
    )
    
    # This would typically be done by admin or automated market data
    messages.info(request, 'Market value updates are performed automatically by the system.')
    return redirect('investments:investment_details', investment_id=investment.id)
