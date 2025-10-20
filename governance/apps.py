# governance/apps.py

from django.apps import AppConfig

class GovernanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'governance'

    def ready(self):
        # IMPORT SIGNALS HERE
        import governance.signals