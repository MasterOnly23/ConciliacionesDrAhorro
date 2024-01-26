from django.contrib import admin
from conciliaciones.models import Extractos, Mayor, Conciliacion

# Register your models here.

class ExtractosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'descripcion', 'monto', 'comprobante', 'codigo', 'observaciones', 'fecha_creacion', 'fecha_modificacion', 'is_deleted')
    search_fields = ('fecha', 'descripcion', 'monto', 'comprobante', 'codigo', 'observaciones', 'fecha_creacion', 'fecha_modificacion', 'is_deleted')
    list_filter = ('fecha', 'descripcion', 'monto', 'comprobante', 'codigo', 'observaciones', 'fecha_creacion', 'fecha_modificacion', 'is_deleted')
    list_per_page = 20

class MayorAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'descripcion', 'monto', 'codigo', 'observaciones', 'fecha_creacion', 'fecha_modificacion', 'is_deleted')
    search_fields = ('fecha', 'descripcion', 'monto', 'codigo', 'observaciones', 'fecha_creacion', 'fecha_modificacion', 'is_deleted')
    list_filter = ('fecha', 'descripcion', 'monto', 'codigo', 'observaciones', 'fecha_creacion', 'fecha_modificacion', 'is_deleted')
    list_per_page = 20

class ConciliacionAdmin(admin.ModelAdmin):
    list_display = ('extracto', 'mayor', 'fecha_conciliacion')
    search_fields = ('extracto', 'mayor', 'fecha_conciliacion')
    list_filter = ('extracto', 'mayor', 'fecha_conciliacion')
    list_per_page = 20

admin.site.register(Extractos)
admin.site.register(Mayor)
admin.site.register(Conciliacion)

