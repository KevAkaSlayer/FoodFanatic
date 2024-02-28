from django.urls import path
from . import views
urlpatterns = [
    path('addcart/<int:product_id>/', views.add_to_cart,name = 'addcart'),
    path('viewcart/', views.view_cart,name = 'cart'),
    path('remove/<int:item_id>/', views.remove_from_cart,name = 'remove'),
    path('review/<int:id>', views.ReviewView,name = 'review'),
    path('detail/<int:id>', views.details,name = 'detail'),
]