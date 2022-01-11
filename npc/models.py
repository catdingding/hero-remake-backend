from django.db import models
from base.models import BaseModel, BaseSkillSetting


class NPC(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    element_type = models.ForeignKey("world.ElementType", on_delete=models.PROTECT)

    hp = models.PositiveIntegerField()
    mp = models.PositiveIntegerField()

    abilities = models.ManyToManyField("ability.Ability")

    has_image = models.BooleanField()


class NPCInfo(BaseModel):
    npc = models.OneToOneField("npc.NPC", on_delete=models.CASCADE, related_name="info")

    description = models.TextField(blank=True)


class NPCAttribute(BaseModel):
    npc = models.ForeignKey("npc.NPC", on_delete=models.CASCADE, related_name="attributes")
    type = models.ForeignKey("world.AttributeType", on_delete=models.PROTECT)
    value = models.IntegerField()

    class Meta:
        unique_together = ('npc', 'type')


class NPCSkillSetting(BaseSkillSetting):
    npc = models.ForeignKey("npc.NPC", on_delete=models.CASCADE, related_name="skill_settings")


class NPCConversation(BaseModel):
    npc = models.ForeignKey("npc.NPC", on_delete=models.CASCADE, related_name="conversations")

    input_content = models.CharField(max_length=100)
    output_content = models.CharField(max_length=100)

    class Meta:
        unique_together = ('npc', 'input_content')


class NPCMessage(BaseModel):
    npc = models.ForeignKey("npc.NPC", on_delete=models.CASCADE, related_name="messages")
    category = models.CharField(max_length=20)
    content = models.CharField(max_length=100)
