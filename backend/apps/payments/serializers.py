from rest_framework import serializers

from .models import Package, Order


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            "id", "name", "slug", "description", "audience", "platform_code",
            "price_amount", "currency", "interval",
        ]


class OrderSerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(source="package.name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "reference", "platform_code", "package_name", "subtotal",
            "discount", "total", "currency", "status", "created_at",
        ]
