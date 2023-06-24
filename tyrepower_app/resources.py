from import_export import resources
from .models import ProxyTyre


class ProxyTyreResource(resources.ModelResource):
    class Meta:
        model = ProxyTyre
        skip_unchanged = True
        report_skipped = False
        name = "Export/Import All Fiels Of Tyres"


class ProxyTyreStockResource(resources.ModelResource):
    class Meta:
        model = ProxyTyre
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('code',)
        fields = ['code', 'total']
        name = "Export/Import Only Stocks of Tyres"