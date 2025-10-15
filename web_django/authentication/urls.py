from django.contrib import admin
from . import views
from django.urls import path,include 
from django.contrib.auth.models import User
urlpatterns = [ 
    path('signup/', views.signup, name="signup"),
    path('signin/', views.signin, name="signin"),
    path('signout/', views.signout, name="signout"),
    path('activate/<uidb64>/<token>/', views.activate, name="activate"),
    path("reset_password/", views.reset_password, name="reset_password"),
    path("reset_password_confirm/<uidb64>/<token>/", views.reset_password_confirm, name="reset_password_confirm"),
    path('guide/', views.guide, name="guide"),
    path('policy/', views.policy, name="policy"),
    path('profile/', views.profile, name="profile"),
    path('update_profile/', views.update_profile, name="update_profile"),
]
