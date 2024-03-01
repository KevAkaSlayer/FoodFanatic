
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from . import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('user.urls')),
    path('menu/', include('menu.urls')),
    path('order/', include('order.urls')),
    path('', views.home,name = 'home'),
    path('category/<slug:category_slug>', views.home,name='catfilter'),
]

urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
