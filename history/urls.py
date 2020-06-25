from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('match', views.match, name="match"),
    path('FAQ', views.FAQ, name="FAQ"),
    path('/riot.txt', views.riot, name="riot")
]