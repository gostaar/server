from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, CustomerBilling, CustomerDelivery, CustomerOrder, CustomerContact, OrderLine, Attachment, OrderAction, OrderComment, CustomerFinancial

class UserAdmin(UserAdmin):
    list_display = ["username","email", "first_name","last_name", "role"]
    fieldsets = (
        (None, {'fields': ('email', 'password', "username", "role")}),
        ("Name", {'fields': ("first_name", "last_name")}),
        ('Permissions', {'fields': (('is_active', 'groups'), )}),
    )

class AttachmentInline(admin.StackedInline):
    model = Attachment
    extra = 0

class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0
    readonly_fields = ("total",)
    fieldsets = [
        (None, {"fields": ["quantity","description","price","total"]}),
    ]

class OrderActionInline(admin.StackedInline):
    model = OrderAction
    extra = 0
    readonly_fields = ("created_at",)

class OrderCommentInline(admin.StackedInline):
    model = OrderComment
    extra = 0
    readonly_fields = ("created_at",)

class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ["delivery","user", "status","total"]
    readonly_fields=('created_at', 'updated_at', "total")
    fieldsets = [
        ("General", {"fields": ["created_at", "updated_at","user", "status"]}),
        (None, {"fields": ["billing", "delivery", "contacts", "customer_comment", "total"]}),
    ]
    inlines = [OrderLineInline,  AttachmentInline, OrderActionInline, OrderCommentInline]

class CustomBillingAdmin(admin.ModelAdmin):
    list_display = ["name", "address1", "zip", "city", "country"]

class CustomerDeliveryAdmin(admin.ModelAdmin):
    list_display = ["name", "address1","zip", "city", "country"]
    
class CustomerFinancialAdmin(admin.ModelAdmin):
    list_display = ["type", "bankDuration", "comment"]

class AttachmentAdmin(admin.ModelAdmin):
    list_display = ["filename","type","mime","size"]

class OrderLineAdmin(admin.ModelAdmin):
    readonly_fields = ("total",)
    list_display = ["quantity","description","price","total"]
    fieldsets = [
        (None, {"fields": ["quantity","description","price","total"]}),
    ]

class OrderActionAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at",)
    list_display = ["user","order","created_at"]

class OrderCommentAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at",)
    list_display = ["user","order","created_at"]

class CustomerContactAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name","mail", "phone"]

admin.site.register(User, UserAdmin)
admin.site.register(CustomerBilling, CustomBillingAdmin)
admin.site.register(CustomerDelivery, CustomerDeliveryAdmin)
admin.site.register(CustomerContact, CustomerContactAdmin)
admin.site.register(CustomerOrder, CustomerOrderAdmin)
admin.site.register(CustomerFinancial, CustomerFinancialAdmin)
admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(OrderLine, OrderLineAdmin)
admin.site.register(OrderAction, OrderActionAdmin)
admin.site.register(OrderComment, OrderCommentAdmin)
