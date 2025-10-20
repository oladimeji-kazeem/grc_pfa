from django.apps import AppConfig

class RiskConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'risk'

    def ready(self):
        # IMPORT SIGNALS HERE
        import risk.signals 
        # Note: You should also update governance/apps.py similarly if not done already
