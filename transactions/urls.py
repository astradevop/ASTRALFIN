from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('add-money/', views.add_money, name='add_money'),
    path('transfer/', views.transfer_money, name='transfer_money'),
    path('history/', views.transaction_history, name='transaction_history'),
    path('statement/', views.statement, name='statement'),
    path('statement/download-pdf/', views.generate_statement_pdf, name='download_statement_pdf'),
]

