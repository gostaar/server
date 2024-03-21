from django.contrib import admin
from .models import Enterprise, Establishment, AlertAddress

class EnterpriseAdmin(admin.ModelAdmin):
    list_display = ["enterpriseNumber","denomination", "zip", "city", "country"]
    search_fields = ["enterpriseNumber", "denomination"]
    ordering = ("enterpriseNumber",)

class EstablishmentAdmin(admin.ModelAdmin):
    raw_id_fields = ["enterprise"]
    list_display = ["establishmentNumber", "enterprise", "commercialDenomination", "zip", "city", "country"]
    search_fields = ["establishmentNumber", "commercialDenomination", "enterprise__enterpriseNumber"]
    ordering = ("establishmentNumber",)

class AlertAdmin(admin.ModelAdmin):
    raw_id_fields = ["enterpriseNumber", "establishmentNumber"]
    readonly_fields=('created_at',)

admin.site.register(Enterprise, EnterpriseAdmin)
admin.site.register(Establishment, EstablishmentAdmin)
admin.site.register(AlertAddress, AlertAdmin)
