from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from bom_app.views import ItemViewSet, update_items ,fetch_project_data,fetch_project_names,submit_create_bom ,delete_items,register, login ,logout,save_bom


router = DefaultRouter()
router.register(r'items', ItemViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/submit-bom/', submit_create_bom, name='submit_bom'),
    path('api/delete-items/', delete_items, name='delete_items'),
    path('api/update-items/',  update_items, name='update_items'),
    path('api/register/', register, name='register'),
    path('api/login/', login, name='login'),
    path('api/logout/', logout, name='logout'),
    path('api/save_bom/',  save_bom, name='save_bom'),
     path('api/fetch_project_names/', fetch_project_names, name='fetch_project_names'),
     path('api/fetch_project_data/', fetch_project_data, name='fetch_project_data')
]
