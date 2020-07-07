from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('match', views.match, name="match"),
    path('region', views.changeRegion, name='region'),
    path('extended', views.loadGameExtension, name="extended"),
    path('FAQ', views.FAQ, name="FAQ"),
    path('/riot.txt', views.riot, name="riot")
]