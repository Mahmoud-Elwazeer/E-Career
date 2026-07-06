"""
Mixin for Job import/export in Django admin.
Compatible with django-unfold + django-import-export.
"""
from import_export.admin import ImportExportMixin
from import_export.formats.base_formats import CSV, XLSX
from .resources import JobResource


class JobImportExportMixin(ImportExportMixin):
    resource_classes = [JobResource]
    import_template_name = "admin/jobs/job/import_guide.html"

    def get_import_formats(self):
        return [CSV, XLSX]

    def get_export_formats(self):
        return [CSV, XLSX]
