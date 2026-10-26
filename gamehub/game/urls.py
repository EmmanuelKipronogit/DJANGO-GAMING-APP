from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("play/", views.play, name="play"),
    path("play/new/", views.new_game, name="new_game"),
    path("play/guess/", views.guess, name="guess"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
]
