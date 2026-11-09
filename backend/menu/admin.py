from django.contrib import admin
from .models import Category, Menu, MenuBundle, MenuBundleItem, OptionGroup, sync_menu_options

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'name')
    list_display = ('id', 'name')
    search_fields = ('name',)
    
@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display       = ('id', 'name', 'category', 'price', 'price_web', 'is_available', 'is_active')
    list_display_links = ('id', 'name')
    list_filter        = ('category', 'is_active')
    search_fields      = ('name',)
    readonly_fields    = ('price_web', 'options')  # options diturunkan dari option_groups

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # M2M baru tersimpan setelah save_model, jadi rakit ulang Menu.options di sini
        sync_menu_options([form.instance.pk])


class MenuBundleItemInline(admin.TabularInline):
    model = MenuBundleItem
    extra = 1


@admin.register(MenuBundle)
class MenuBundleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'is_available')
    list_display_links = ('id', 'name')
    inlines = [MenuBundleItemInline]


@admin.register(OptionGroup)
class OptionGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'required', 'multiple')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
