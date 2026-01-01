from django import forms
from .models import Investment, InvestmentTransaction

class InvestmentForm(forms.ModelForm):
    """
    Form for creating a new investment
    """
    class Meta:
        model = Investment
        fields = ['investment_type', 'investment_name', 'principal_amount', 
                  'expected_return_rate', 'maturity_date', 'risk_level', 'notes']
        widgets = {
            'investment_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-teal-500/50 focus:bg-white/8'
            }),
            'investment_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-teal-500/50 focus:bg-white/8',
                'placeholder': 'e.g., HDFC Balanced Fund'
            }),
            'principal_amount': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-teal-500/50 focus:bg-white/8',
                'placeholder': 'Enter amount to invest',
                'step': '0.01'
            }),
            'expected_return_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-teal-500/50 focus:bg-white/8',
                'placeholder': 'e.g., 12.5',
                'step': '0.01'
            }),
            'maturity_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-teal-500/50 focus:bg-white/8',
                'type': 'date'
            }),
            'risk_level': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-teal-500/50 focus:bg-white/8'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-teal-500/50 focus:bg-white/8',
                'placeholder': 'Any additional notes...',
                'rows': 3
            }),
        }
        labels = {
            'investment_type': 'Investment Type',
            'investment_name': 'Investment Name',
            'principal_amount': 'Investment Amount (₹)',
            'expected_return_rate': 'Expected Return Rate (% per annum)',
            'maturity_date': 'Maturity Date',
            'risk_level': 'Risk Level',
            'notes': 'Notes'
        }


class WithdrawInvestmentForm(forms.Form):
    """
    Form for withdrawing/closing an investment
    """
    confirm_withdrawal = forms.BooleanField(
        required=True,
        label='I confirm I want to withdraw this investment',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-teal-600 bg-gray-100 border-gray-300 rounded focus:ring-teal-500'
        })
    )
    withdrawal_amount = forms.DecimalField(
        required=True,
        label='Withdrawal Amount (₹)',
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-teal-500/50 focus:bg-white/8',
            'placeholder': 'Enter amount to withdraw',
            'step': '0.01'
        })
    )

