from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Item

# Register Item model
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('head', 'make', 'mat_name', 'type_no', 'least_price', 'discount')
    search_fields = ('head', 'make', 'mat_name', 'type_no')
