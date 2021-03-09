from django.db import models
from base.models import BaseModel


class Log(BaseModel):
    type = models.CharField(max_length=20)
    content = models.CharField(max_length=400)


class PublicChatMessage(BaseModel):
    sender = models.ForeignKey("chara.Chara", on_delete=models.PROTECT)
    content = models.CharField(max_length=400)


class CountryChatMessage(BaseModel):
    country = models.ForeignKey("country.Country", null=True, on_delete=models.PROTECT)
    sender = models.ForeignKey("chara.Chara", on_delete=models.PROTECT)
    content = models.CharField(max_length=400)


class PrivateChatMessage(BaseModel):
    sender = models.ForeignKey("chara.Chara", related_name="sent_chat_messages", on_delete=models.PROTECT)
    receiver = models.ForeignKey("chara.Chara", related_name="received_chat_messages", on_delete=models.PROTECT)
    content = models.CharField(max_length=400)
