from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('auth/', include('accounts.urls')),
    path('banking/', include('banking.urls')),
    path('transactions/', include('transactions.urls')),
    path('loans/', include('loans.urls')),
    path('investments/', include('investments.urls')),
    path('oauth/', include('social_django.urls', namespace='social')),
]
