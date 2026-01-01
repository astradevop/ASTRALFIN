from django import forms
from .models import Account
import re

class AccountCreationForm(forms.ModelForm):
    """
    Form for creating a new bank account
    """
    class Meta:
        model = Account
        fields = [
            'account_holder_name', 
            'phone_number', 
            'pan_number', 
            'aadhar_number', 
            'date_of_birth', 
            'gender', 
            'address'
        ]
        widgets = {
            'account_holder_name': forms.TextInput(attrs={
                'placeholder': 'Enter your full name',
                'required': 'required'
            }),
            'phone_number': forms.TextInput(attrs={
                'placeholder': 'Enter 10-digit mobile number',
                'required': 'required'
            }),
            'pan_number': forms.TextInput(attrs={
                'placeholder': 'ABCDE1234F',
                'style': 'text-transform: uppercase;',
                'required': 'required'
            }),
            'aadhar_number': forms.TextInput(attrs={
                'placeholder': '123456789012',
                'required': 'required'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'required': 'required'
            }),
            'gender': forms.Select(attrs={
                'required': 'required'
            }),
            'address': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Enter your complete residential address',
                'required': 'required'
            })
        }
        labels = {
            'account_holder_name': 'Full Name',
            'phone_number': 'Mobile Number',
            'pan_number': 'PAN Card Number',
            'aadhar_number': 'Aadhar Card Number',
            'date_of_birth': 'Date of Birth',
            'gender': 'Gender',
            'address': 'Residential Address'
        }
        help_texts = {
            'account_holder_name': 'Enter your full name as per government ID',
            'phone_number': 'Enter valid 10-digit mobile number',
            'pan_number': 'Enter 10-character PAN number (e.g., ABCDE1234F)',
            'aadhar_number': 'Enter 12-digit Aadhar number',
            'date_of_birth': 'Select your date of birth',
            'gender': 'Select your gender',
            'address': 'Enter your complete residential address'
        }
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        
        if not phone_number:
            raise forms.ValidationError('Phone number is required.')
        
        # Check if phone number is numeric and 10 digits
        if not phone_number.isdigit():
            raise forms.ValidationError('Phone number must contain only digits.')
        
        if len(phone_number) != 10:
            raise forms.ValidationError('Phone number must be exactly 10 digits.')
        
        # Check for duplicate
        if Account.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError('An account with this phone number already exists.')
        
        return phone_number
    
    def clean_pan_number(self):
        pan_number = self.cleaned_data.get('pan_number')
        
        if not pan_number:
            raise forms.ValidationError('PAN number is required.')
        
        pan_number = pan_number.upper()
        
        # PAN format: 5 letters, 4 digits, 1 letter
        pan_pattern = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')
        
        if not pan_pattern.match(pan_number):
            raise forms.ValidationError('Invalid PAN format. It should be like ABCDE1234F.')
        
        # Check for duplicate
        if Account.objects.filter(pan_number=pan_number).exists():
            raise forms.ValidationError('An account with this PAN number already exists.')
        
        return pan_number
    
    def clean_aadhar_number(self):
        aadhar_number = self.cleaned_data.get('aadhar_number')
        
        if not aadhar_number:
            raise forms.ValidationError('Aadhar number is required.')
        
        # Check if aadhar is numeric and 12 digits
        if not aadhar_number.isdigit():
            raise forms.ValidationError('Aadhar number must contain only digits.')
        
        if len(aadhar_number) != 12:
            raise forms.ValidationError('Aadhar number must be exactly 12 digits.')
        
        # Check for duplicate
        if Account.objects.filter(aadhar_number=aadhar_number).exists():
            raise forms.ValidationError('An account with this Aadhar number already exists.')
        
        return aadhar_number
    
    def clean_date_of_birth(self):
        from datetime import date
        dob = self.cleaned_data.get('date_of_birth')
        
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            if age < 18:
                raise forms.ValidationError('You must be at least 18 years old to open an account.')
            
            if age > 120:
                raise forms.ValidationError('Please enter a valid date of birth.')
        
        return dob


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile/account details
    Only phone_number, address, and gender are editable
    """
    class Meta:
        model = Account
        fields = [
            'phone_number',
            'address',
            'gender'
        ]
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'placeholder': 'Enter 10-digit mobile number',
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 text-white placeholder-slate-400'
            }),
            'address': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Enter your complete residential address',
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 text-white placeholder-slate-400'
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 text-white'
            })
        }
        labels = {
            'phone_number': 'Mobile Number',
            'address': 'Residential Address',
            'gender': 'Gender'
        }
    
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        
        if not phone_number:
            raise forms.ValidationError('Phone number is required.')
        
        # Check if phone number is numeric and 10 digits
        if not phone_number.isdigit():
            raise forms.ValidationError('Phone number must contain only digits.')
        
        if len(phone_number) != 10:
            raise forms.ValidationError('Phone number must be exactly 10 digits.')
        
        # Check for duplicate (exclude current account)
        existing = Account.objects.filter(phone_number=phone_number).exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError('An account with this phone number already exists.')
        
        # If phone number changed, mark as unverified
        if self.instance and self.instance.phone_number != phone_number:
            self.instance.phone_verified = False
        
        return phone_number

