from django.apps import AppConfig
from . import scheduler
GLOBALSCHEDULE = None
class GameConfig(AppConfig):
    name = 'game'

    def ready(self):             
        scheduler.start()
