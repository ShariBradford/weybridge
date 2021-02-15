from django.contrib import admin
from .models import *

# admin.site.register(Backlog)
@admin.register(Backlog)
class BacklogAdmin(admin.ModelAdmin):
    # fields = ('app_name', 'model_name', 'title', 'description', 'category', 'priority','status')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_by','created_at','updated_by','updated_at')
    search_fields = ('title', 'app_name','model_name','description')
    list_display = ('title', 'app_name', 'model_name', 'category', 'priority','status')
    list_filter = ('app_name','model_name','category', 'priority','status')

    def save_model(self, request, obj, form, change):
        print(f"Saving {obj.title}. Change = {change}")
        if change:
            # user is updating item 
            obj.updated_by = request.user
        else:
            # user is creating item
            obj.created_by = request.user
            obj.updated_by = request.user

        super().save_model(request, obj, form, change)


