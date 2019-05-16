from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins
from rest_framework.exceptions import ValidationError as DRFValidationError


class CreateModelMixin(mixins.CreateModelMixin):
    def perform_update(self, serializer):
        try:
            return super(CreateModelMixin, self).perform_create(serializer=serializer)
        except DjangoValidationError as e:
            raise DRFValidationError(e.message)


class ListModelMixin(mixins.ListModelMixin):
    pass


class RetrieveModelMixin(mixins.RetrieveModelMixin):
    pass


class DestroyModelMixin(mixins.DestroyModelMixin):
    def perform_destroy(self, instance):
        try:
            instance.delete()
        except DjangoValidationError as e:
            raise DRFValidationError(e.message)


class UpdateModelMixin(mixins.UpdateModelMixin):
    def perform_update(self, serializer):
        try:
            return super(UpdateModelMixin, self).perform_update(serializer=serializer)
        except DjangoValidationError as e:
            raise DRFValidationError(e.message)
