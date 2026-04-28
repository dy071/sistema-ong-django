from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Conectando as rotas
    path('materiais/', include('materiais.urls')),
]