from django.urls import path, include
from . import views

urlpatterns = [
	#Pages
    path('', views.home, name="home"),
    path('FAQ', views.FAQ, name="FAQ"),
    path('legal', views.legal, name="legal"),
    path('live_game', views.live_game, name="live_game"),
    path('lobby', views.lobby, name="lobby"),
    path('/riot.txt', views.riot, name="riot"),

    #Posts
    path('match', views.loadMatches, name="match"),
    path('extended', views.loadGameExtension, name="extended"),
    path('region', views.changeRegion, name='region'),
    path('live', views.checkLiveStatus, name='live')
]