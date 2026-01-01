from django.urls import path
from . import views

app_name = 'banking'

urlpatterns = [
    path('create-account/', views.create_account, name='create_account'),
    path('account-details/', views.account_details, name='account_details'),
    path('view-balance/', views.view_balance, name='view_balance'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('send-verification/', views.send_verification_code, name='send_verification'),
    path('verify-phone-form/', views.verify_phone_form, name='verify_phone_form'),
    path('verify-phone/', views.verify_phone, name='verify_phone'),
]

