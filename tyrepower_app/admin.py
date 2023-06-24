from django.contrib import admin
from .models import *
from .resources import *
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin.widgets import AdminFileWidget
from import_export.admin import ImportExportModelAdmin


admin.site.site_title = "Tyre Power"
admin.site.site_header = "Tyre Power Administration"
admin.site.index_title = "Tyre Power Administration"



class AdminImageWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        output = []
        if value and getattr(value, "url", None):
            image_url = value.url
            file_name = str(value)
            output.append(
                f'<a href="{image_url}" target="_blank">'
                f'<img src="{image_url}" alt="{file_name}" width="150" height="150" '
                f'style="object-fit: cover;"/> </a>')
        output.append(super(AdminFileWidget, self).render(name, value, attrs, renderer))
        return mark_safe(u''.join(output))


class UserModelAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'phone', 'tier', 'is_active', 'action', 'detail', 'created_at', 'updated_at', )
    list_filter = ('tier', 'is_active', 'created_at')
    fieldsets = (
        ('User Credentials', {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email', 'phone', 'first_name', 'last_name', 'tier')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important Dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'first_name', 'last_name', 'tier', 'is_staff', 'is_superuser', 'password1', 'password2'),
        }),
    )
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')
    ordering = ('id', 'username', 'email', 'phone', 'first_name', 'last_name', 'created_at', 'updated_at')
    list_per_page = 20
    list_max_show_all = 10000000
    filter_horizontal = ()
    readonly_fields = ('last_login', 'created_at', 'updated_at')

    def action(self, obj):
        if obj.id:
            return mark_safe("<a class='button btn' style='color:green; padding:0 1rem; ' href='/admin/tyrepower_app/user/{}/change/'>Edit</a>".format(obj.id)
                             + "    " + "<a class='button btn' style='color:red; padding:0 1rem; ' href='/admin/tyrepower_app/user/{}/delete/'>Delete</a>".format(obj.id))
        else:
            social_button = '<a  href="#">---</a>'
            return mark_safe(u''.join(social_button))
        
    def detail(self, obj):
        if obj.id:
            return mark_safe("<a class='retailer-detail-btn' style='color:blue; padding:0 1rem; ' href='/retailer-detail/admin/{}/'>Detail</a>".format(obj.id))
        else:
            social_button = '<a  href="#">---</a>'
            return mark_safe(u''.join(social_button))
admin.site.register(User, UserModelAdmin)
admin.site.unregister(Group)


@admin.register(Tier)
class TierAdmin(admin.ModelAdmin):
    list_display = ['id', 'tier', 'discount_percentage', 'created_at', 'updated_at']
    search_fields = ('tier',)
    ordering = ('id', 'tier', 'created_at', 'updated_at')
    list_per_page = 20
    list_max_show_all = 10000000
    filter_horizontal = ()
    list_filter = ['tier', 'discount_percentage', 'created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ['id', 'image_tag', 'name', 'created_at', 'updated_at']
    search_fields = ('name',)
    ordering = ('id', 'name', 'created_at', 'updated_at')
    list_per_page = 20
    list_max_show_all = 10000000
    filter_horizontal = ()
    list_filter = ['created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')
    formfield_overrides = {
        models.ImageField: {'widget': AdminImageWidget}
    }


@admin.register(ProxyTyre)
class ProxyTyreAdmin(ImportExportModelAdmin):
    resource_classes = [ProxyTyreResource, ProxyTyreStockResource]
    list_display = ['id', 'logo', 'name', 'code', 'total', 'brand', 'size', 'flag', 'offer', 'created_at', 'updated_at']
    search_fields = ('name', 'code', 'brand', 'size', 'created_at', 'updated_at')
    ordering = ('id', 'name', 'code', 'total', 'brand', 'size', 'created_at', 'updated_at')
    list_per_page = 20
    list_max_show_all = 10000000
    filter_horizontal = ()
    filter_vertical = ()
    list_filter = ('offer', 'brand', 'size', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

    def flag(self, obj):
        if obj.total<=10:
            return mark_safe('<img src="http://69.49.235.253:8088/static/images/Red_flag.png" height="30" width="30" alt="red">')
        else:
            return mark_safe('<img src="http://69.49.235.253:8088/static/images/Green_flag.png" height="30" width="30" alt="red">')
    
    def logo(self, obj):
        if Manufacturer.objects.filter(name=obj.brand):
            manufacturer = Manufacturer.objects.get(name=obj.brand)
            return mark_safe(f'<img src="{manufacturer.logo.url}" height="60" width="60" alt="red">')
        return None


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'tyre', 'total_number', 'total_price', 'status', 'created_at', 'updated_at']
    search_fields = ('user__username', 'user__email', 'user__phone', 'user__first_name', 'user__last_name', 'tyre__name', 'total_number', 'created_at', 'updated_at')
    ordering = ('id', 'user', 'tyre', 'total_number', 'total_price', 'status', 'created_at', 'updated_at')
    list_per_page = 20
    filter_horizontal = ()
    list_filter = ['user', 'tyre', 'status', 'created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'PO_number', 'user', 'status', 'created_at', 'updated_at']
    search_fields = ('PO_number', 'user__username', 'user__email', 'user__phone', 'user__first_name', 'user__last_name', 'tyre__name', 'total_number', 'total_price', 'status', 'created_at', 'updated_at')
    ordering = ('order_id', 'PO_number', 'user', 'status', 'created_at', 'updated_at')
    list_per_page = 20
    list_max_show_all = 10000000
    filter_horizontal = ()
    list_filter = ['user', 'tyre', 'status', 'product_delivery', 'created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['id', 'retailer', 'name', 'phone', 'created_at', 'updated_at']
    search_fields = ('retailer__username', 'name', 'phone',)
    ordering = ('id', 'retailer', 'name', 'phone', 'created_at', 'updated_at')
    list_per_page = 20
    list_max_show_all = 10000000
    filter_horizontal = ()
    list_filter = ['postcode', 'created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')



@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'heading', 'created_at', 'updated_at']
    search_fields = ('heading', 'created_at', 'updated_at')
    ordering = ('id', 'heading', 'created_at', 'updated_at')
    list_per_page = 20
    list_max_show_all = 10000000
    filter_horizontal = ()
    list_filter = ['sender', 'receiver', 'created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TopSearch)
class TopSearchAdmin(admin.ModelAdmin):
    list_display = ['id', 'word', 'retailer', 'created_at', 'updated_at']
    search_fields = ('word', 'retailer__username',  'created_at', 'updated_at')
    ordering = ('id', 'word',  'created_at', 'updated_at')
    list_per_page = 20
    list_max_show_all = 10000000
    filter_horizontal = ()
    list_filter = ['created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ['id', 'privacy_policy', 'created_at', 'updated_at']
    search_fields = ('privacy_policy',)
    ordering = ('id', 'privacy_policy', 'created_at', 'updated_at')
    list_per_page = 20
    list_max_show_all = 10000000
    filter_horizontal = ()
    list_filter = ['created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TermAndCondition)
class TermAndConditionAdmin(admin.ModelAdmin):
    list_display = ['id', 'terms', 'created_at', 'updated_at']
    search_fields = ('terms',)
    ordering = ('id', 'terms', 'created_at', 'updated_at')
    list_per_page = 20
    list_max_show_all = 10000000
    filter_horizontal = ()
    list_filter = ['created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')


