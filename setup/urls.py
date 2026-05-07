from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from materiais import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('materiais/', include('materiais.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('cadastro_usuario/', views.cadastro_usuario, name='cadastro_usuario'),]