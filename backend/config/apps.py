from django.contrib.admin.apps import AdminConfig


class AleraAdminConfig(AdminConfig):
    default_site = 'config.admin_site.AleraAdminSite'
