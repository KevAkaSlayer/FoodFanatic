from django.urls import path
from . import views
urlpatterns = [
    path('placeorder/', views.place_order,name = 'placeorder'),
    path('order_details/<int:id>', views.order_details,name = 'order_details'),
    path('product_list', views.product_list,name = 'product_list'),
]