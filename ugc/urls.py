from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()

router.register(r'monsters', views.UGCMonsterViewSet)
router.register(r'dungeons', views.UGCDungeonViewSet)

urlpatterns = [

] + router.urls
