from django.urls import path
from . import views
urlpatterns = [
    path('addcart/<int:id>', views.add_to_cart,name = 'addcart'),
    path('viewcart/', views.view_cart,name = 'cart'),
    path('remove/<int:id>', views.remove_from_cart,name = 'remove'),
    path('review/<int:id>', views.Review,name = 'review'),
    path('detail/<int:id>', views.detail,name = 'detail'),
]