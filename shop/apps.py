from django.apps import AppConfig
from  django.db.models.signals import post_save


class ShopConfig(AppConfig):
    name = 'shop'

    def ready(self):
        # print('SHOP APP READY')
        from . import signals
