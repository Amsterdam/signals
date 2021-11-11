# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.contrib import admin, messages
from django.contrib.gis.admin import OSMGeoAdmin
from django.db import transaction
from django.db.models import Q

from signals.apps.dsl.ExpressionEvaluator import ExpressionEvaluator
from signals.apps.signals import workflow
from signals.apps.signals.models import (
    Area,
    Category,
    CategoryDepartment,
    CategoryQuestion,
    Department,
    Expression,
    ExpressionContext,
    ExpressionType,
    Question,
    RoutingExpression,
    Signal,
    Source,
    Status,
    StatusMessageTemplate
)


class CategoryQuestionInline(admin.StackedInline):
    raw_id_fields = ('category', 'question',)
    model = CategoryQuestion
    extra = 1


class QuestionAdmin(admin.ModelAdmin):
    inlines = (CategoryQuestionInline, )
    fields = ('key', 'field_type', 'meta', 'required')
    list_display = ('key', 'field_type', 'meta', 'required')
    ordering = ('-key',)
    list_per_page = 20
    list_select_related = True
    list_filter = ['category__slug']


admin.site.register(Question, QuestionAdmin)


class ParentCategoryFilter(admin.SimpleListFilter):
    title = 'Parent category'
    parameter_name = 'parent__id'

    def lookups(self, request, model_admin):
        return [
            (category.pk, category.__str__())
            for category in Category.objects.filter(parent__isnull=True).iterator()
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(Q(parent__id=self.value()) | Q(id=self.value()))
        return queryset.all()


class CategoryAdmin(admin.ModelAdmin):
    fields = ('name', 'parent', 'is_active', 'description', 'handling_message')
    list_display = ('name', 'slug', 'parent', 'is_active', 'description', 'handling_message')
    ordering = ('parent__name', 'name',)
    list_per_page = 20
    list_filter = (ParentCategoryFilter,)

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Category, CategoryAdmin)


class CategoryDepartmentInline(admin.TabularInline):
    raw_id_fields = ('category', 'department',)
    model = CategoryDepartment
    extra = 0


class DepartmentAdmin(admin.ModelAdmin):
    inlines = (CategoryDepartmentInline, )
    fields = ('code', 'name', 'is_intern', 'can_direct')
    list_display = ('code', 'name', 'is_intern', 'can_direct')
    ordering = ('name',)
    list_per_page = 20


admin.site.register(Department, DepartmentAdmin)


class AreaAdmin(OSMGeoAdmin):
    search_fields = ['name', 'code', '_type__name', '_type__code']
    list_display = ['name', 'code', '_type']
    list_filter = ['_type__code']


admin.site.register(Area, AreaAdmin)


class ChildCategoryFilter(admin.SimpleListFilter):
    title = 'Child category'
    parameter_name = 'category_id'

    def lookups(self, request, model_admin):
        return [
            (category.pk, category.__str__())
            for category in Category.objects.iterator()
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category__id=self.value())
        return queryset.all()


class StatusMessageTemplatesAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'state', 'order', 'text',)
    list_display_links = list_display
    list_filter = (ChildCategoryFilter,)


admin.site.register(StatusMessageTemplate, StatusMessageTemplatesAdmin)


class SignalAdmin(admin.ModelAdmin):
    """
    signals.Signal model admin, allows some maintenance tasks.
    """
    fields = ('id', 'created_at', 'updated_at', 'get_status_display', 'get_category')
    list_display = ('id', 'created_at', 'updated_at', 'get_status_display', 'get_category')
    list_display_links = None  # change page not relevant
    ordering = ('-id',)
    list_per_page = 20
    list_select_related = True
    search_fields = ['id__exact']  # we do not want to page through 400k or more signals

    # Add an action that frees signals stuck between SIA and CityControl. These
    # signals need to be in workflow.VERZONDEN state.
    actions = ['free_signals']

    def free_signals(self, request, queryset):
        filtered_signals = queryset.filter(status__state=workflow.VERZONDEN)

        with transaction.atomic():
            updated_signal_ids = []
            for signal in filtered_signals:
                new_status = Status(
                    _signal=signal,
                    state=workflow.AFGEHANDELD_EXTERN,
                    text='Vastgelopen melding vrijgegeven zonder tussenkomst CityControl.',
                    created_by=request.user.email
                )
                new_status.save()
                signal.status = new_status
                signal.save()
                updated_signal_ids.append(signal.id)

            if updated_signal_ids:
                msg = 'Successfully freed the following IDs: {}'.format(','.join(
                    str(_id) for _id in updated_signal_ids
                ))
            else:
                msg = 'No IDs were freed.'

            transaction.on_commit(lambda: self.message_user(request, msg))

    free_signals.short_description = 'Free SIA signals (meldingen) stuck in state VERZONDEN.'

    # Get the human readable status and category:
    def get_status_display(self, obj):
        return obj.status.get_state_display()

    get_status_display.short_description = 'status'

    def get_category(self, obj):
        return obj.category_assignment.category.name

    get_category.short_description = 'category'

    # Disable editing on this model (change page customization)
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Signal, SignalAdmin)


class SourceAdmin(admin.ModelAdmin):
    fields = ('name', 'description', 'is_active', 'is_public', 'order', )


admin.site.register(Source, SourceAdmin)


class RoutingExpressionAdmin(admin.ModelAdmin):
    list_filter = ['_expression___type__name', '_department__code']
    list_display = ['_expression', '_department', 'is_active']

    def save_model(self, request, obj, form, change):
        # if is_active is true, try to compile code, deactivate when invalid
        try:
            if obj.is_active:
                expr = form.cleaned_data.get('_expression', None)
                if expr:
                    ExpressionEvaluator().compile(expr.code)
        except Exception as e:
            obj.is_active = False
            messages.add_message(request, messages.WARNING, f'Rule deactivated due to error in expression: {str(e)}')

        super().save_model(request, obj, form, change)


admin.site.register(RoutingExpression, RoutingExpressionAdmin)


class ExpressionAdmin(admin.ModelAdmin):
    list_filter = ['_type__name']


admin.site.register(Expression, ExpressionAdmin)


class ExpressionTypeAdmin(admin.ModelAdmin):
    pass


admin.site.register(ExpressionType, ExpressionTypeAdmin)


class ExpressionContextAdmin(admin.ModelAdmin):
    list_filter = ['_type__name']


admin.site.register(ExpressionContext, ExpressionContextAdmin)
