import pandas as pd
from django.contrib import admin, messages
from django import forms
from django.db.models import F
from django.http import FileResponse, HttpResponse
from django.urls import reverse, path
from django.utils.html import format_html

from signals.apps.classification.models import Classifier
from signals.apps.classification.tasks import train_classifier
import openpyxl

from signals.apps.signals import workflow
from signals.apps.signals.models import Category, Signal


class RunTrainingForm(admin.helpers.ActionForm):
    use_signals_in_database_for_training = forms.ChoiceField(
        choices=((False, "Nee"), (True, "Ja")),
        label='Neem meldingen uit Signalen mee',
        required=False
    )


class TrainingSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'file', )
    actions = ["run_training_with_training_set"]
    action_form = RunTrainingForm

    @admin.action(description="Train model met geselecteerde dataset")
    def run_training_with_training_set(self, request, queryset):
        """
        Run validation, if validation fails show an error message.

        First we validate if there are no missing columns (Main, Sub and Text column are required), after this we check if there is atleast one row of data (next
        to the headers)
        """
        training_set_ids = []
        use_signals_in_database_for_training = request.POST['use_signals_in_database_for_training']

        for training_set in queryset:
            file = training_set.file

            wb = openpyxl.load_workbook(file)
            first_sheet = wb.active

            # Check if there are any missing columns
            headers = [cell.value for cell in first_sheet[1]]
            required_columns = ["Main", "Sub", "Text"]
            missing_columns = [col for col in required_columns if col not in headers]

            if missing_columns:
                self.message_user(
                    request,
                    f"Training set { training_set.name } is missing required columns: {', '.join(missing_columns)}",
                    messages.ERROR,
                )

                return

            # Check if the training set contains any data rows
            data_rows = list(first_sheet.iter_rows(min_row=2, values_only=True))
            if not any(data_rows):
                self.message_user(
                    request,
                    f"The training set { training_set.name } does not contain any data rows.",
                    messages.ERROR
                    )
                return

            # Check if there are no sub categories present in the training set that are not present in the database
            sub_col_index = headers.index("Sub")
            subcategory_values = {row[sub_col_index] for row in data_rows if row[sub_col_index]}
            existing_subcategories = set(Category.objects.filter(name__in=subcategory_values).values_list('name', flat=True))
            missing_subcategories = subcategory_values - existing_subcategories

            if missing_subcategories:
                self.message_user(
                    request,
                    f"The training set {training_set.name} contains unknown sub categories: {', '.join(missing_subcategories)}. Add these to Signalen before continuing.",
                    messages.ERROR
                )
                return

            # Check if there are no main categories present in the training set that are not present in the database
            main_col_index = headers.index("Main")
            maincategory_values = {row[main_col_index] for row in data_rows if row[main_col_index]}
            existing_maincategories = set(
                Category.objects.filter(name__in=maincategory_values).values_list('name', flat=True))
            missing_maincategories = maincategory_values - existing_maincategories

            if missing_maincategories:
                self.message_user(
                    request,
                    f"The training set {training_set.name} contains unknown main categories: {', '.join(missing_maincategories)}. Add these to Signalen before continuing.",
                    messages.ERROR
                )
                return

            training_set_ids.append(training_set.id)

        # Training will fail if any subcategory or main category appears in only one signal,
        # when use_signals_in_database_for_training is set to True
        if use_signals_in_database_for_training and use_signals_in_database_for_training != "False":
            signals = Signal.objects.filter(
                status__state=workflow.AFGEHANDELD,
                category_assignment__category__is_active=True,
                category_assignment__category__parent__is_active=True
            ).exclude(
                category_assignment__category__slug="overig",
                category_assignment__category__parent__slug="overig"
            ).values(
                'text',
                sub_category=F('category_assignment__category__name'),
                main_category=F('category_assignment__category__parent__name'),
            )

            data = [{
                "Sub": signal["sub_category"],
                "Main": signal["main_category"],
                "Text": signal["text"]
            } for signal in signals]

            signals_df = pd.DataFrame(data)

            sub_counts = signals_df['Sub'].value_counts()
            main_counts = signals_df['Main'].value_counts()

            sub_issues = sub_counts[sub_counts == 1]
            main_issues = main_counts[main_counts == 1]

            if sub_issues.any() or main_issues.any():
                parts = []

                if not sub_issues.empty:
                    sub_list = ", ".join(map(str, sub_issues.index))
                    parts.append(f"sub categories: {sub_list}")

                if not main_issues.empty:
                    main_list = ", ".join(map(str, main_issues.index))
                    parts.append(f"main categories: {main_list}")

                message = (
                        "The database contains not the minimum of two signals with " +
                        " and ".join(parts)
                )

                self.message_user(
                    request,
                    message,
                    messages.ERROR
                )
                return

        train_classifier.delay(training_set_ids, use_signals_in_database_for_training)

        self.message_user(
            request,
            "Training of the model has been initiated. This can take a few minutes.",
            messages.SUCCESS,
        )


class ClassifierAdmin(admin.ModelAdmin):
    """
    Creating or disabling classifiers by hand in the Admin interface is disabled,

    a successful training job should create his own classifier object.
    """
    list_display = ('name', 'precision', 'recall', 'accuracy', 'is_active', )
    actions = ["activate_classifier"]
    readonly_fields = ('training_status', 'training_error', 'download_main_confusion_matrix', 'download_sub_confusion_matrix',)

    @admin.action(description="Maak deze classifier actief")
    def activate_classifier(self, request, queryset):
        """
        Make the chosen classifier active, disable other classifiers
        """

        if queryset.count() > 1:
            self.message_user(
                request,
                "You can only make one classifier active.",
                messages.ERROR
            )
            return

        try:
            Classifier.objects.update(is_active=False)
            Classifier.objects.filter(id=queryset.first().id).update(is_active=True)

            self.message_user(
                request,
                f"Classifier { queryset.first().name } has been activated.",
                messages.SUCCESS
            )
        except Exception:
            self.message_user(
                request,
                f"Classifier { queryset.first().name } has not been activated.",
                messages.ERROR
            )

    fieldsets = (
        (None, {
            'fields': (
                'name',
                'download_main_confusion_matrix',
                'download_sub_confusion_matrix',
                'precision',
                'recall',
                'accuracy',
                'is_active',
                'training_status',
                'training_error',
            )
        }),
    )

    def download_main_confusion_matrix(self, obj):
        if obj.main_confusion_matrix:
            url = reverse('admin:classification_classifier_download', args=[obj.pk, 'main_confusion_matrix'])

            return format_html(
                '<a href="{}" class="button" style="padding:6px 12px; background:#007bff; color:white; border-radius:4px;">Download main confusion matrix</a>',
                url
            )
        return "No file found"

    def download_sub_confusion_matrix(self, obj):
        if obj.sub_confusion_matrix:
            url = reverse('admin:classification_classifier_download', args=[obj.pk, 'sub_confusion_matrix'])

            return format_html(
                '<a href="{}" class="button" style="padding:6px 12px; background:#007bff; color:white; border-radius:4px;">Download sub confusion matrix</a>',
                url
            )
        return "No file found"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<path:object_id>/download/<str:field_name>/',
                 self.admin_site.admin_view(self.download_file),
                 name='classification_classifier_download'),
        ]
        return my_urls + urls

    def download_file(self, request, object_id, field_name):
        obj = self.get_object(request, object_id)
        file_field = getattr(obj, field_name)
        if file_field:
            response = FileResponse(file_field.open('rb'))
            response['Content-Disposition'] = f'attachment; filename="{file_field.name.split("/")[-1]}"'
            return response
        return HttpResponse("File not found", status=404)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True
