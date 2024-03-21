from rest_framework import serializers
from .models import Enterprise, Establishment

class EnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enterprise
        fields = ["enterpriseNumber", "denomination","commercialDenomination","city", "zip", "street", "number", "box", "extraAddressInfo","country"]
    
class EstablishmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Establishment
        fields = ["establishmentNumber", "enterprise", "denomination","commercialDenomination","city", "zip", "street", "number", "box", "extraAddressInfo","country"]

    