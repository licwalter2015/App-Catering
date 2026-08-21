from django.contrib import admin

from .models import Domain, Tenant


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 1


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'deposit_percentage', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [DomainInline]


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('domain',)


class TenantAdminMixin(admin.ModelAdmin):
    """
    Mixin para modelos que pertenecen a un tenant.
    Filtra automáticamente por el tenant del usuario logueado
    y asigna el tenant al crear nuevos registros.
    """

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.tenant:
            return qs.filter(tenant=request.user.tenant)
        return qs

    def save_model(self, request, obj, form, change):
        if not change and request.user.tenant:
            obj.tenant = request.user.tenant
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if request.user.tenant and 'tenant' in form.base_fields:
            form.base_fields['tenant'].initial = request.user.tenant
            form.base_fields['tenant'].widget = admin.widgets.AdminTextInputWidget(
                attrs={'readonly': 'readonly', 'style': 'display:none'}
            )
        return form
