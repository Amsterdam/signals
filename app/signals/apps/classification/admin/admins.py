from django.contrib import admin, messages


class TrainingSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'file', )
    actions = ["run_training_with_dataset"]

    @admin.action(description="Train model met geselecteerde dataset")
    def run_training_with_dataset(self, request, queryset):
        """
        TODO: run actual training with dataset
        """
        self.message_user(
            request,
            "Training of the model has been initiated.",
            messages.SUCCESS,
        )


class ClassifierAdmin(admin.ModelAdmin):
    """
    Creating or disabling classifiers by hand in the Admin interface is disabled,

    a successful training job should create his own classifier object.
    """
    list_display = ('name',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True
