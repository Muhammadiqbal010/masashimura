from django.contrib import admin
from .models import Category, Menu, MenuBundle, MenuBundleItem

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
    readonly_fields    = ('price_web',)


class MenuBundleItemInline(admin.TabularInline):
    model = MenuBundleItem
    extra = 1


@admin.register(MenuBundle)
class MenuBundleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'is_available')
    list_display_links = ('id', 'name')
    inlines = [MenuBundleItemInline]
