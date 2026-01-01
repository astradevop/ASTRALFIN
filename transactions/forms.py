from django import forms
from django.contrib.auth import get_user_model
from banking.models import Account

User = get_user_model()

class AddMoneyForm(forms.Form):
    """
    Form for adding money to user's own account (self top-up)
    """
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'placeholder': 'Enter amount'
        }),
        label='Amount (₹)'
    )
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'placeholder': 'Add a note (optional)'
        }),
        label='Description'
    )


class TransferByMobileForm(forms.Form):
    """
    Form for transferring money using recipient's mobile number
    """
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'placeholder': 'Enter recipient phone number'
        }),
        label='Recipient Phone Number'
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'placeholder': 'Enter amount'
        }),
        label='Amount (₹)'
    )
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'placeholder': 'Add a note (optional)'
        }),
        label='Description'
    )
    
    def clean_phone_number(self):
        """Validate that phone number exists and has an account"""
        phone_number = self.cleaned_data.get('phone_number')
        try:
            Account.objects.get(phone_number=phone_number)
        except Account.DoesNotExist:
            raise forms.ValidationError('No account found with this phone number.')
        return phone_number


class TransferByAccountForm(forms.Form):
    """
    Form for transferring money using account number and IFSC code
    """
    account_number = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'placeholder': 'Enter 10-digit account number'
        }),
        label='Account Number'
    )
    ifsc_code = forms.CharField(
        max_length=11,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'placeholder': 'Enter IFSC code',
            'value': 'NEOBANKX'
        }),
        label='IFSC Code'
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'placeholder': 'Enter amount'
        }),
        label='Amount (₹)'
    )
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'placeholder': 'Add a note (optional)'
        }),
        label='Description'
    )
    
    def clean(self):
        """Validate that account exists"""
        cleaned_data = super().clean()
        account_number = cleaned_data.get('account_number')
        ifsc_code = cleaned_data.get('ifsc_code')
        
        if account_number and ifsc_code:
            try:
                Account.objects.get(account_number=account_number, ifsc_code=ifsc_code)
            except Account.DoesNotExist:
                raise forms.ValidationError('No account found with this account number and IFSC code.')
        
        return cleaned_data


class StatementFilterForm(forms.Form):
    """
    Form for filtering transaction statements by date range
    """
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
        }),
        label='From Date'
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
        }),
        label='To Date'
    )


class TransactionSearchForm(forms.Form):
    """
    Form for searching and filtering transactions
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-teal-500/50 focus:bg-white/8',
            'placeholder': 'Search by description...'
        }),
        label='Search'
    )
    transaction_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types'), ('Deposit', 'Deposit'), ('Transfer', 'Transfer'), ('Withdrawal', 'Withdrawal')],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-teal-500/50 focus:bg-white/8'
        }),
        label='Type'
    )
    min_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-teal-500/50 focus:bg-white/8',
            'placeholder': 'Min amount',
            'step': '0.01'
        }),
        label='Min Amount'
    )
    max_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-teal-500/50 focus:bg-white/8',
            'placeholder': 'Max amount',
            'step': '0.01'
        }),
        label='Max Amount'
    )

