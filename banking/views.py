from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import random
import requests
import json
from .models import Account
from .forms import AccountCreationForm, ProfileUpdateForm

@login_required
def create_account(request):
    # Check if user already has an account
    if hasattr(request.user, 'account'):
        messages.warning(request, 'You already have an account.')
        return redirect('banking:account_details')
    
    if request.method == 'POST':
        form = AccountCreationForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            
            # Update user's account creation status
            request.user.is_account_created = True
            request.user.save()
            
            messages.success(request, f'Congratulations! Your account has been created successfully. Account Number: {account.account_number}')
            return redirect('banking:account_details')
    else:
        form = AccountCreationForm()
    
    return render(request, 'banking/create_account.html', {'form': form})


@login_required
def account_details(request):
    try:
        account = request.user.account
    except Account.DoesNotExist:
        messages.error(request, 'You do not have a bank account yet. Please create one.')
        return redirect('banking:create_account')
    
    return render(request, 'banking/account_details.html', {'account': account})


@login_required
def view_balance(request):
    try:
        account = request.user.account
    except Account.DoesNotExist:
        messages.error(request, 'You do not have a bank account yet. Please create one.')
        return redirect('banking:create_account')
    
    return render(request, 'banking/view_balance.html', {'account': account})


@login_required
def send_verification_code(request):
    try:
        account = request.user.account
    except Account.DoesNotExist:
        messages.error(request, 'You do not have a bank account yet.')
        return redirect('banking:create_account')
    
    if account.phone_verified:
        messages.info(request, 'Your phone number is already verified.')
        return redirect('banking:account_details')
    
    if not account.phone_number:
        messages.error(request, 'No phone number associated with your account.')
        return redirect('banking:account_details')
    
    phone = account.phone_number
    if not phone.startswith('+'):
        phone = '+91' + phone
    
    verification_code = str(random.randint(100000, 999999))
    
    account.phone_verification_code = verification_code
    account.phone_verification_sent_at = timezone.now()
    account.save()
    
    # SIMULATION: In a real app, you would integrate with an SMS gateway
    # Since we are removing Auth0, we will just show the code in a message for the user
    messages.info(request, f'Verification code generated for {phone}')
    messages.warning(request, f'SIMULATED SMS: Your verification code is {verification_code}')
    
    return redirect('banking:verify_phone_form')
    
    return redirect('banking:verify_phone_form')


@login_required
def verify_phone_form(request):
    try:
        account = request.user.account
    except Account.DoesNotExist:
        messages.error(request, 'You do not have a bank account yet.')
        return redirect('banking:create_account')
    
    if account.phone_verified:
        messages.info(request, 'Your phone number is already verified.')
        return redirect('banking:account_details')
    
    return render(request, 'banking/verify_phone.html', {'account': account})


@login_required
def verify_phone(request):
    try:
        account = request.user.account
    except Account.DoesNotExist:
        messages.error(request, 'You do not have a bank account yet.')
        return redirect('banking:create_account')
    
    if request.method == 'POST':
        code = request.POST.get('verification_code', '').strip()
        
        if not account.phone_verification_sent_at:
            messages.error(request, 'No verification code was sent. Please request a new code.')
            return redirect('banking:account_details')
        
        # Check if code is expired (10 minutes validity)
        expiry_time = account.phone_verification_sent_at + timedelta(minutes=10)
        if timezone.now() > expiry_time:
            messages.error(request, 'Verification code has expired. Please request a new code.')
            account.phone_verification_code = None
            account.phone_verification_sent_at = None
            account.save()
            return redirect('banking:account_details')
        
        # Format phone number
        phone = account.phone_number
        if not phone.startswith('+'):
            phone = '+91' + phone  # Default to India (+91)
        
        # Verify code locally (Auth0 removed)
        if code == account.phone_verification_code:
            account.phone_verified = True
            account.phone_verification_code = None
            account.phone_verification_sent_at = None
            account.save()
            messages.success(request, '✅ Phone number verified successfully!')
            return redirect('banking:account_details')
        else:
            messages.error(request, '❌ Invalid verification code. Please try again.')
            return redirect('banking:verify_phone_form')
    
    return redirect('banking:account_details')


@login_required
def update_profile(request):
    try:
        account = request.user.account
    except Account.DoesNotExist:
        messages.error(request, 'You do not have a bank account yet. Please create one first.')
        return redirect('banking:create_account')
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=account)
        if form.is_valid():
            updated_account = form.save()
            
            # Check if phone number was changed
            if 'phone_number' in form.changed_data:
                messages.info(request, '📱 Phone number updated. Please verify your new phone number.')
            
            messages.success(request, '✅ Profile updated successfully!')
            return redirect('banking:account_details')
    else:
        form = ProfileUpdateForm(instance=account)
    
    context = {
        'form': form,
        'account': account
    }
    return render(request, 'banking/update_profile.html', context)
