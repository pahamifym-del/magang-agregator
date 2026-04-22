from django.apps import AppConfig


class InternshipsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # Nama harus sama persis dengan path di INSTALLED_APPS
    name = "apps.internships"
    verbose_name = "Lowongan Magang"