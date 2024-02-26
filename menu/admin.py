from django.contrib import admin
from . import models 
# Register your models here.
admin.site.register(models.FoodItem)
admin.site.register(models.CartItem)
admin.site.register(models.Review)

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

admin.site.register(models.Category,CategoryAdmin)