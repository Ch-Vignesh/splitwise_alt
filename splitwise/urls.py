"""splitwise URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from divvy import views


urlpatterns = [
    path('admin/', admin.site.urls),

    # Home page and user authentication
    path('', views.homePage, name='home'),
    path('register/', views.register_user, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.user_profile, name='profile'),

    # User-related views and API
    path('users/', views.UserListCreateAPIView.as_view(), name='user-list-create'),
    path('add_user/', views.add_user, name='add_user'),

    # Expense-related views and API
    path('add_expense/', views.add_expense, name='add_expense'),
    path('expenses/', views.show_expenses, name='show_expenses'),
    path('expenses/<int:user_id>/', views.show_expenses, name='user_expenses'),
    path('show_expenses/', views.show_expenses, name='show_expenses'),

    # If you'd like to make the 'add_expense' an API route instead of a regular view, you can use the following:
    # path('api/add_expense/', views.add_expense, name='api-add-expense'),  # Uncomment if API-based expense is needed
]
