from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/risk/', include('risk.urls')), 
    # Add other apps later: path('api/governance/', include('governance.urls')), etc.
    
    # Frontend will be served from the root later, but for development API is separate
]
