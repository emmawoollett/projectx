from django.urls import path

from . import api

urlpatterns = (
    path("user/", api.user, name="user_api_user"),
    path("login/", api.login, name="user_api_login"),
    path("logout/", api.logout, name="user_api_logout"),
    path("reset_password/", api.reset_password, name="user_api_reset_password"),
    path("reset_password_check/", api.reset_password_check, name="user_api_reset_password_check"),
    path("reset_password_complete/", api.reset_password_complete, name="user_api_reset_password_complete"),
)
