from django.contrib import admin, messages
from django.utils.translation import ngettext
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
    list_editable = ('app_name','model_name','status','priority', 'category')
    actions = ['mark_completed']

    def mark_completed(self, request, queryset):
        updated = queryset.update(status = Backlog.Status.COMPLETED)
        self.message_user(
            request, 
            ngettext(
                f"{updated} item successfully marked as completed.", 
                f"{updated} items successfully marked as completed.", 
                updated
            ),
            level=messages.SUCCESS, 
            extra_tags='', 
            fail_silently=True
        )
        for obj in queryset:
            self.log_change(request, obj, f"Marked completed: '{str(obj)}'")
    mark_completed.short_description='Mark selected items completed'

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


