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
    
    try:
        auth0_domain = settings.SOCIAL_AUTH_AUTH0_DOMAIN
        client_id = settings.SOCIAL_AUTH_AUTH0_KEY
        client_secret = settings.SOCIAL_AUTH_AUTH0_SECRET
        
        sms_url = f'https://{auth0_domain}/passwordless/start'
        sms_payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'connection': 'sms',
            'phone_number': phone,
            'send': 'code'
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        sms_response = requests.post(sms_url, json=sms_payload, headers=headers)
        
        if sms_response.status_code in [200, 201]:
            messages.success(request, f'✅ Verification code sent to {account.phone_number} via SMS')
        else:
            # Log the error for debugging
            error_data = sms_response.json() if sms_response.text else {}
            error_message = error_data.get('error_description', error_data.get('message', sms_response.text))
            
            # Fallback: Show code if SMS fails
            messages.warning(request, f'SMS service unavailable. Your verification code is: {verification_code}')
            messages.error(request, f'Auth0 Error: {error_message}')
            messages.info(request, f'Status Code: {sms_response.status_code}')
            
    except Exception as e:
        # Fallback: Show code if any error occurs
        messages.warning(request, f'SMS service unavailable. Your verification code is: {verification_code}')
        messages.error(request, f'Error: {str(e)}')
    
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
        
        # Verify code with Auth0
        try:
            auth0_domain = settings.SOCIAL_AUTH_AUTH0_DOMAIN
            client_id = settings.SOCIAL_AUTH_AUTH0_KEY
            client_secret = settings.SOCIAL_AUTH_AUTH0_SECRET
            
            # Call Auth0's token endpoint to verify the OTP
            verify_url = f'https://{auth0_domain}/oauth/token'
            verify_payload = {
                'grant_type': 'http://auth0.com/oauth/grant-type/passwordless/otp',
                'client_id': client_id,
                'client_secret': client_secret,
                'username': phone,
                'otp': code,
                'realm': 'sms',
                'scope': 'openid profile email'
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            verify_response = requests.post(verify_url, json=verify_payload, headers=headers)
            
            if verify_response.status_code == 200:
                # Code is valid!
                account.phone_verified = True
                account.phone_verification_code = None
                account.phone_verification_sent_at = None
                account.save()
                messages.success(request, '✅ Phone number verified successfully!')
                return redirect('banking:account_details')
            else:
                # Invalid code or other error
                error_data = verify_response.json() if verify_response.text else {}
                error_description = error_data.get('error_description', 'Invalid verification code')
                
                messages.error(request, f'❌ {error_description}')
                return redirect('banking:verify_phone_form')
                
        except Exception as e:
            messages.error(request, f'❌ Verification failed: {str(e)}')
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
