from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from bom_app.views import ItemViewSet, update_price ,submit_create_bom ,delete_items,register, login ,logout


router = DefaultRouter()
router.register(r'items', ItemViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/submit-bom/', submit_create_bom, name='submit_bom'),
    path('api/delete-items/', delete_items, name='delete_items'),
    path('api/update-price/',  update_price, name=' update_price'),
    path('api/register/', register, name='register'),
    path('api/login/', login, name='login'),
    path('api/logout/', logout, name='logout'),
]
