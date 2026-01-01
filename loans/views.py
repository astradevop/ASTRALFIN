from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction as db_transaction
from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import Loan, EMIPayment
from .forms import LoanApplicationForm, ManualEMIPaymentForm, AutopayToggleForm, LoanPreclosureForm
from transactions.models import Transaction

@login_required
def apply_loan(request):
    # Check if user has an account
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    if request.method == 'POST':
        form = LoanApplicationForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.account = request.user.account
            loan.save()
            
            messages.success(request, f'Your loan application for ₹{loan.loan_amount} has been submitted successfully. EMI: ₹{loan.monthly_emi}/month')
            return redirect('loans:loan_status')
    else:
        form = LoanApplicationForm()
    
    return render(request, 'loans/apply_loan.html', {'form': form})


@login_required
def loan_status(request):
    # Check if user has an account
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    loans = Loan.objects.filter(account=request.user.account).order_by('-application_date')
    
    # Calculate counts
    pending_count = loans.filter(loan_status='Pending').count()
    approved_count = loans.filter(loan_status='Approved').count()
    rejected_count = loans.filter(loan_status='Rejected').count()
    
    context = {
        'loans': loans,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    
    return render(request, 'loans/loan_status.html', context)


@login_required
def loan_details(request, loan_id):
    # Check if user has an account
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    loan = get_object_or_404(Loan, id=loan_id, account=request.user.account)
    
    # Calculate loan details
    monthly_emi = float(loan.monthly_emi) if loan.monthly_emi else 0
    total_payable = monthly_emi * loan.tenure_months
    total_interest = total_payable - float(loan.loan_amount)
    
    context = {
        'loan': loan,
        'monthly_emi': monthly_emi,
        'total_interest': total_interest,
        'total_payable': total_payable,
    }
    
    return render(request, 'loans/loan_details.html', context)


@login_required
def emi_schedule(request, loan_id):
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    loan = get_object_or_404(Loan, id=loan_id, account=request.user.account)
    
    if loan.loan_status != 'Disbursed':
        messages.warning(request, 'EMI schedule is only available for disbursed loans.')
        return redirect('loans:loan_details', loan_id=loan.id)
    
    # Get all EMI payments
    emi_payments = loan.emi_payments.all().order_by('emi_number')
    
    # Calculate summary
    total_paid = loan.emi_payments.filter(payment_status='Paid').aggregate(
        total=models.Sum('paid_amount')
    )['total'] or 0
    
    context = {
        'loan': loan,
        'emi_payments': emi_payments,
        'total_paid': total_paid,
    }
    
    return render(request, 'loans/emi_schedule.html', context)


@login_required
def pay_emi_manual(request, loan_id):
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    loan = get_object_or_404(Loan, id=loan_id, account=request.user.account)
    
    if loan.loan_status != 'Disbursed':
        messages.error(request, 'You can only pay EMI for active loans.')
        return redirect('loans:loan_details', loan_id=loan.id)
    
    # Get next pending EMI
    next_emi = loan.emi_payments.filter(payment_status='Pending').order_by('emi_number').first()
    
    if not next_emi:
        messages.info(request, 'All EMIs have been paid!')
        return redirect('loans:emi_schedule', loan_id=loan.id)
    
    # Check if user has sufficient balance
    account = request.user.account
    if account.balance < next_emi.emi_amount:
        messages.error(request, f'Insufficient balance. You need ₹{next_emi.emi_amount} to pay this EMI. Current balance: ₹{account.balance}')
        return redirect('loans:emi_schedule', loan_id=loan.id)
    
    if request.method == 'POST':
        form = ManualEMIPaymentForm(request.POST)
        if form.is_valid():
            with db_transaction.atomic():
                # Re-fetch EMI with lock to prevent race conditions
                next_emi = EMIPayment.objects.select_for_update().get(id=next_emi.id)
                
                # Double-check EMI is still pending (prevent double payment)
                if next_emi.payment_status != 'Pending':
                    messages.warning(request, f'EMI #{next_emi.emi_number} has already been paid.')
                    return redirect('loans:emi_schedule', loan_id=loan.id)
                
                # Deduct EMI amount from account
                account.balance -= next_emi.emi_amount
                account.save()
                
                # Update EMI payment (mark as paid with Manual method)
                # NOTE: Autopay logic should check payment_status='Pending' before attempting to pay
                next_emi.paid_amount = next_emi.emi_amount
                next_emi.payment_date = timezone.now()
                next_emi.payment_status = 'Paid'
                next_emi.payment_method = 'Manual'
                next_emi.transaction_reference = f'EMI-{loan.id}-{next_emi.emi_number}'
                next_emi.save()
                
                # Update loan details
                loan.remaining_balance -= next_emi.emi_amount
                
                # Update next EMI date
                next_pending = loan.emi_payments.filter(payment_status='Pending').order_by('emi_number').first()
                if next_pending:
                    loan.next_emi_date = next_pending.due_date
                else:
                    # All EMIs paid, close the loan
                    loan.loan_status = 'Closed'
                    loan.closure_date = timezone.now()
                    loan.next_emi_date = None
                
                loan.save()
                
                # Create transaction record
                Transaction.objects.create(
                    from_account=account,
                    to_account=None,
                    amount=next_emi.emi_amount,
                    transaction_type='Withdrawal',
                    status='Success',
                    description=f'EMI Payment #{next_emi.emi_number} - {loan.loan_type} Loan',
                    balance_after=account.balance,
                    account=account
                )
                
                if loan.loan_status == 'Closed':
                    messages.success(request, f'✅ EMI #{next_emi.emi_number} paid successfully! 🎉 Your loan is now fully paid and closed!')
                else:
                    messages.success(request, f'✅ EMI #{next_emi.emi_number} paid successfully! Amount: ₹{next_emi.emi_amount}')
                
                return redirect('loans:emi_schedule', loan_id=loan.id)
    else:
        form = ManualEMIPaymentForm()
    
    context = {
        'loan': loan,
        'next_emi': next_emi,
        'form': form,
        'account_balance': account.balance,
    }
    
    return render(request, 'loans/pay_emi_manual.html', context)


@login_required
def toggle_autopay(request, loan_id):
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    loan = get_object_or_404(Loan, id=loan_id, account=request.user.account)
    
    if loan.loan_status != 'Disbursed':
        messages.error(request, 'Autopay is only available for active loans.')
        return redirect('loans:loan_details', loan_id=loan.id)
    
    if request.method == 'POST':
        form = AutopayToggleForm(request.POST)
        if form.is_valid():
            autopay_enabled = form.cleaned_data['autopay_enabled']
            loan.autopay_enabled = autopay_enabled
            loan.save()
            
            if autopay_enabled:
                messages.success(request, '✅ Autopay enabled successfully! EMIs will be automatically deducted on due dates.')
            else:
                messages.info(request, 'ℹ️ Autopay disabled. You will need to pay EMIs manually.')
            
            return redirect('loans:emi_schedule', loan_id=loan.id)
    else:
        form = AutopayToggleForm(initial={'autopay_enabled': loan.autopay_enabled})
    
    context = {
        'loan': loan,
        'form': form,
    }
    
    return render(request, 'loans/toggle_autopay.html', context)


@login_required
def preclose_loan(request, loan_id):
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    loan = get_object_or_404(Loan, id=loan_id, account=request.user.account)
    
    if loan.loan_status != 'Disbursed':
        messages.error(request, 'You can only preclose active loans.')
        return redirect('loans:loan_details', loan_id=loan.id)
    
    # Calculate preclosure amount (remaining balance)
    preclosure_amount = loan.remaining_balance or 0
    
    account = request.user.account
    
    # Check if user has sufficient balance
    if account.balance < preclosure_amount:
        messages.error(request, f'Insufficient balance. You need ₹{preclosure_amount} to preclose this loan. Current balance: ₹{account.balance}')
        return redirect('loans:emi_schedule', loan_id=loan.id)
    
    if request.method == 'POST':
        form = LoanPreclosureForm(request.POST, preclosure_amount=preclosure_amount)
        if form.is_valid():
            with db_transaction.atomic():
                # Re-fetch loan with lock to prevent race conditions
                loan = Loan.objects.select_for_update().get(id=loan.id)
                
                # Verify loan is still in Disbursed status
                if loan.loan_status != 'Disbursed':
                    messages.warning(request, 'This loan has already been closed or is not active.')
                    return redirect('loans:loan_details', loan_id=loan.id)
                
                # Deduct preclosure amount from account
                account.balance -= preclosure_amount
                account.save()
                
                # Mark all pending EMIs as paid (only those that are still pending)
                # This ensures that if any EMI was paid manually, it won't be double-charged
                pending_emis = loan.emi_payments.filter(payment_status='Pending').select_for_update()
                
                if not pending_emis.exists():
                    messages.info(request, 'All EMIs have already been paid!')
                    return redirect('loans:loan_details', loan_id=loan.id)
                
                for emi in pending_emis:
                    emi.paid_amount = emi.emi_amount
                    emi.payment_date = timezone.now()
                    emi.payment_status = 'Paid'
                    emi.payment_method = 'Preclosure'
                    emi.transaction_reference = f'PRECLOSURE-{loan.id}'
                    emi.save()
                
                # Close the loan
                loan.remaining_balance = 0
                loan.loan_status = 'Closed'
                loan.closure_date = timezone.now()
                loan.next_emi_date = None
                loan.save()
                
                # Create transaction record
                Transaction.objects.create(
                    from_account=account,
                    to_account=None,
                    amount=preclosure_amount,
                    transaction_type='Withdrawal',
                    status='Success',
                    description=f'Loan Preclosure - {loan.loan_type} Loan (Full Payment)',
                    balance_after=account.balance,
                    account=account
                )
                
                messages.success(request, f'🎉 Loan preclosed successfully! Amount paid: ₹{preclosure_amount}. Your loan is now fully settled!')
                return redirect('loans:loan_details', loan_id=loan.id)
    else:
        form = LoanPreclosureForm(preclosure_amount=preclosure_amount)
    
    # Count pending EMIs
    pending_emis_count = loan.emi_payments.filter(payment_status='Pending').count()
    
    context = {
        'loan': loan,
        'form': form,
        'preclosure_amount': preclosure_amount,
        'pending_emis_count': pending_emis_count,
        'account_balance': account.balance,
    }
    
    return render(request, 'loans/preclose_loan.html', context)
