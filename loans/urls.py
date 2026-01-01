from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    path('apply/', views.apply_loan, name='apply_loan'),
    path('status/', views.loan_status, name='loan_status'),
    path('details/<int:loan_id>/', views.loan_details, name='loan_details'),
    path('<int:loan_id>/emi-schedule/', views.emi_schedule, name='emi_schedule'),
    path('<int:loan_id>/pay-emi/', views.pay_emi_manual, name='pay_emi_manual'),
    path('<int:loan_id>/toggle-autopay/', views.toggle_autopay, name='toggle_autopay'),
    path('<int:loan_id>/preclose/', views.preclose_loan, name='preclose_loan'),
]

