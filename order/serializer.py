from rest_framework import serializers
from .models import OrderAction, OrderComment, User, CustomerBilling, CustomerDelivery, CustomerContact, OrderLine, Attachment, CustomerOrder

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "username", "role"]

class BillingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerBilling
        fields = "__all__"

class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerDelivery
        fields = "__all__"

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerContact
        fields = "__all__"

class OrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLine
        fields = ["quantity", "description", "price", "total"]

class AttachmentSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    class Meta:
        model = Attachment
        fields = ["id","type", "mime","size", "url", "filename"]
    def get_type(self,obj):
        return obj.get_type_display()
    
class OrderActionSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = OrderAction
        fields = ["description","created_at","user", "additionalContext"]

class OrderCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = OrderComment
        fields = ["description","created_at","user"]

class CustomerOrderSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    status = serializers.SerializerMethodField()
    user = UserSerializer()
    billing = BillingSerializer()
    delivery = DeliverySerializer()
    contacts = ContactSerializer(many=True)
    customer_comment = serializers.CharField()
    order_lines = OrderLineSerializer(many=True)
    attachment_files = AttachmentSerializer(many=True)
    total = serializers.SerializerMethodField()
    order_history = OrderActionSerializer(many=True)
    order_comments = OrderCommentSerializer(many=True)

    class Meta:
        model = CustomerOrder
        fields="__all__"

    def get_status(self,obj):
        return obj.get_status_display()
    
    def get_total(self, obj):
        return obj.total()
    
    

    
