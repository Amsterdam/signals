from rest_framework import serializers

from signals.apps.api.v1.fields import CategoryHyperlinkedRelatedField
from signals.apps.signals.models import CategoryAssignment


class _NestedCategoryModelSerializer(serializers.ModelSerializer):
    sub_category = CategoryHyperlinkedRelatedField(write_only=True, required=True,
                                                   source='category')
    sub = serializers.CharField(source='category.name', read_only=True)
    sub_slug = serializers.CharField(source='category.slug', read_only=True)
    main = serializers.CharField(source='category.parent.name', read_only=True)
    main_slug = serializers.CharField(source='category.parent.slug', read_only=True)

    category_url = serializers.SerializerMethodField(read_only=True)
    text = serializers.CharField(required=False)

    departments = serializers.SerializerMethodField(
        source='category.departments',
        read_only=True
    )

    class Meta:
        model = CategoryAssignment
        fields = (
            'category_url',
            'sub',
            'sub_slug',
            'main',
            'main_slug',
            'sub_category',
            'departments',
            'created_by',
            'text',
        )
        read_only_fields = (
            'created_by',
            'departments',
        )

    def get_departments(self, obj):
        return ', '.join(obj.category.departments.values_list('code', flat=True))

    def get_category_url(self, obj):
        from rest_framework.reverse import reverse
        request = self.context['request'] if 'request' in self.context else None
        return reverse(
            'v1:category-detail',
            kwargs={
                'slug': obj.category.parent.slug,
                'sub_slug': obj.category.slug,
            },
            request=request
        )
