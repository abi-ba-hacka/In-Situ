from django.conf.urls import include, url
from .views import BotView
urlpatterns = [
                  url(r'^chat/?$', BotView.as_view()) 
               ]
