from django import forms
from .models import Loan, EMIPayment

class LoanApplicationForm(forms.ModelForm):
    """
    Form for applying for a loan
    """
    class Meta:
        model = Loan
        fields = ['loan_type', 'loan_amount', 'interest_rate', 'tenure_months', 'purpose']
        widgets = {
            'loan_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
            }),
            'loan_amount': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
                'placeholder': 'Enter loan amount'
            }),
            'interest_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
                'placeholder': 'Enter interest rate (e.g., 10.5)',
                'step': '0.01'
            }),
            'tenure_months': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
                'placeholder': 'Enter tenure in months'
            }),
            'purpose': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
                'placeholder': 'Describe the purpose of the loan',
                'rows': 4
            }),
        }
        labels = {
            'loan_type': 'Loan Type',
            'loan_amount': 'Loan Amount (₹)',
            'interest_rate': 'Interest Rate (% per annum)',
            'tenure_months': 'Tenure (Months)',
            'purpose': 'Purpose of Loan'
        }
        help_texts = {
            'loan_amount': 'Enter the amount you wish to borrow',
            'interest_rate': 'Annual interest rate',
            'tenure_months': 'Loan repayment period in months',
        }


class ManualEMIPaymentForm(forms.Form):
    """
    Form for manual EMI payment
    """
    confirm_payment = forms.BooleanField(
        required=True,
        label='I confirm I want to pay this EMI',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-teal-600 bg-gray-100 border-gray-300 rounded focus:ring-teal-500'
        })
    )


class AutopayToggleForm(forms.Form):
    """
    Form for enabling/disabling autopay
    """
    autopay_enabled = forms.BooleanField(
        required=False,
        label='Enable Auto-Pay for EMI',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-teal-600 bg-gray-100 border-gray-300 rounded focus:ring-teal-500'
        })
    )


class LoanPreclosureForm(forms.Form):
    """
    Form for loan preclosure confirmation
    """
    confirm_preclosure = forms.BooleanField(
        required=True,
        label='I confirm I want to preclose this loan',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-teal-600 bg-gray-100 border-gray-300 rounded focus:ring-teal-500'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.preclosure_amount = kwargs.pop('preclosure_amount', 0)
        super().__init__(*args, **kwargs)
    
    def clean_confirm_preclosure(self):
        confirm = self.cleaned_data.get('confirm_preclosure')
        if not confirm:
            raise forms.ValidationError('You must confirm to proceed with loan preclosure.')
        return confirm

