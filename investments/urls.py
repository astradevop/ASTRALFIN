from django.urls import path
from . import views

app_name = 'investments'

urlpatterns = [
    path('', views.investment_dashboard, name='investment_dashboard'),
    path('create/', views.create_investment, name='create_investment'),
    path('portfolio/', views.portfolio_view, name='portfolio_view'),
    path('<int:investment_id>/', views.investment_details, name='investment_details'),
    path('<int:investment_id>/withdraw/', views.withdraw_investment, name='withdraw_investment'),
    path('<int:investment_id>/update-value/', views.update_investment_value, name='update_investment_value'),
]

