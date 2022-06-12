from django.urls import path
from rest_framework.routers import SimpleRouter

from adventure import views

router = SimpleRouter()

router.register(r'adventures', views.AdventureViewSet)

urlpatterns = [

] + router.urls
