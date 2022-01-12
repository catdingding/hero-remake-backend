from django.db import models
from base.models import BaseModel


class ChangeLog(BaseModel):
    category = models.CharField(max_length=20)
    content = models.TextField()
    note = models.TextField()
    time = models.DateTimeField()


class Log(BaseModel):
    category = models.CharField(max_length=20)
    content = models.TextField()


class PublicChatMessage(BaseModel):
    sender = models.ForeignKey("chara.Chara", on_delete=models.PROTECT)
    content = models.CharField(max_length=400)


class CountryChatMessage(BaseModel):
    country = models.ForeignKey("country.Country", null=True, on_delete=models.PROTECT)
    sender = models.ForeignKey("chara.Chara", on_delete=models.PROTECT)
    content = models.CharField(max_length=400)


class TeamChatMessage(BaseModel):
    team = models.ForeignKey("team.Team", null=True, on_delete=models.SET_NULL)
    sender = models.ForeignKey("chara.Chara", on_delete=models.PROTECT)
    content = models.CharField(max_length=400)


class PrivateChatMessage(BaseModel):
    sender = models.ForeignKey("chara.Chara", related_name="sent_chat_messages", on_delete=models.PROTECT)
    receiver = models.ForeignKey("chara.Chara", related_name="received_chat_messages", on_delete=models.PROTECT)
    content = models.CharField(max_length=400)

    is_system_generated = models.BooleanField(default=False)
