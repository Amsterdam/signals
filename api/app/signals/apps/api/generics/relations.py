from rest_framework import relations
from rest_framework.reverse import reverse


class ParameterisedHyperlinkedRelatedField(relations.HyperlinkedRelatedField):
    lookup_fields = (('pk', 'pk'),)

    def __init__(self, *args, **kwargs):
        self.lookup_fields = kwargs.pop('lookup_fields', self.lookup_fields)
        super(ParameterisedHyperlinkedRelatedField, self).__init__(*args, **kwargs)

    def use_pk_only_optimization(self):
        return False

    def get_object(self, view_name, view_args, view_kwargs):
        kwargs = {}
        for model_field, url_param in self.lookup_fields:
            model_field = model_field.replace('.', '__')
            kwargs[model_field] = view_kwargs[url_param]
        return self.get_queryset().get(**kwargs)

    def get_url(self, obj, view_name, request, format):
        kwargs = {}
        for model_field, url_param in self.lookup_fields:
            attr = obj
            for field in model_field.split('.'):
                if hasattr(attr, field):
                    attr = getattr(attr, field)
            kwargs[url_param] = attr
        return reverse(view_name, kwargs=kwargs, request=request, format=format)


class ParameterisedHyperLinkedIdentityField(ParameterisedHyperlinkedRelatedField):
    def __init__(self, view_name=None, **kwargs):
        assert view_name is not None, 'The `view_name` argument is required.'
        kwargs['read_only'] = True
        kwargs['source'] = '*'
        super(ParameterisedHyperLinkedIdentityField, self).__init__(view_name, **kwargs)
