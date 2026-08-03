from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),  
    path('recherche/', include('recherche.urls', namespace='recherche')),
    path('appointments/', include('appointments.urls', namespace='appointments')),  
]
