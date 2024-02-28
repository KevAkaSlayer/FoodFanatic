from django.urls import path
from . import views

urlpatterns = [
    path('register/',views.signup_user.as_view(),name='register'),
    path('login/',views.login_user.as_view(),name='login'),
    path('logout/',views.userlogout,name='logout'),
    path('verify/<str:token>',views.verify,name='verify')
]