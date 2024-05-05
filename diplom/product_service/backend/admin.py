from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from backend.models import User, Shop, Category, Product, ProductInfo, \
    Parameter, ProductParameter, Order, OrderItem, \
    Contact, ConfirmEmailToken
from django.utils.safestring import mark_safe
from import_export import resources
from import_export.admin import ImportExportModelAdmin


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Панель управления пользователями
    """
    model = User

    fieldsets = (
        (None, {'fields': ('email', 'password', 'type',)}),
        ('Personal info',
         {'fields': (
             'first_name', 'last_name', 'company', 'position',
             'avatar_thumbnail',

         )}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',
                       'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    list_display = (
        'id', 'first_name', 'last_name', 'email', 'is_staff',
        'type',
        'company',
        'position', 'is_active', 'post_photo')

    list_display_links = ['id', 'first_name', 'last_name',
                          'email']  # кликабельность полей
    ordering = ['last_name']  # сортировка
    list_editable = ['is_staff']  # можно редактировать
    list_per_page = 5  # пагинация
    actions = ['set_pub']
    search_fields = ['last_name__startswith']  # список полей поиск
    # list_filter = ['is_active'] # фильтр
    # fields = ['id','last_name'] # поля которые можно редактировать по умолчанию можно все
    # exclude = ['last_name'] # кроме полей которые можно редактировать
    readonly_fields = [
        'last_name']  # поля только для чтения которые нельзя редактировать

    @admin.action(description='Статус персонала')
    def set_pub(request, queryset):
        queryset.update(set_pub=User.Status.PUBLISHED)

    # admin_thumbnail = AdminThumbnail(image_field='thumbnail')

    @admin.display(description='Фото')
    def post_photo(self, user: User):
        if user.avatar_thumbnail:
            return mark_safe(
                f"<img src='{user.avatar_thumbnail.url}'.width=50>")
        return "Без фото"


@admin.register(Shop)
class ShopAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'name', 'url', 'state', 'user']
    list_display_links = ['id', 'name']
    search_fields = ['name__startswith']
    list_per_page = 15


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'name']
    list_display_links = ['id', 'name']
    search_fields = ['name__startswith']
    list_per_page = 15


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'name', 'category']
    list_display_links = ['id', 'name']
    search_fields = ['name', 'category__name']
    list_per_page = 15


@admin.register(ProductInfo)
class ProductInfoAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'model', 'external_id', 'quantity', 'price',
                    'price_rrc', 'product', 'shop']

    list_display_links = ['id', 'model']
    search_fields = ['model', 'shop__name']
    list_per_page = 15


@admin.register(Parameter)
class ParameterAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'name']
    list_display_links = ['id', 'name']
    search_fields = ['name']
    list_per_page = 15


@admin.register(ProductParameter)
class ProductParameterAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'value', 'parameter', 'product_info_id']
    list_display_links = ['id', 'value', 'parameter']
    list_per_page = 15


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    pass
    list_display = ['id', 'user', 'dt', 'state', 'contact']
    list_display_links = ['id', 'user']
    search_fields = ['user__last_name', 'user__first_name']
    list_editable = ['state']
    actions = ['set_pub']
    list_per_page = 15

    @admin.action(description='Статус')
    def set_pub(request, queryset):
        queryset.update(set_pub=Order.Status.PUBLISHED)


@admin.register(OrderItem)
class OrderItemAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'quantity', 'order', 'product_info_id']
    list_display_links = ['id', 'quantity']
    list_per_page = 15


@admin.register(Contact)
class ContactAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'user', 'city', 'street', 'house', 'structure',
                    'building', 'apartment', 'phone']
    list_display_links = ['id', 'user']
    search_fields = ['user__last_name', 'user__first_name']
    list_per_page = 15


@admin.register(ConfirmEmailToken)
class ConfirmEmailTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'key', 'created_at',)
    list_display_links = ['id', 'user']
    search_fields = ['user__last_name', 'user__first_name']
