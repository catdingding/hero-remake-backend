from django.db import models
from base.models import BaseModel


class Team(BaseModel):
    name = models.CharField(max_length=10)
    leader = models.OneToOneField("chara.Chara", null=True, related_name="leader_of", on_delete=models.SET_NULL)


class TeamJoinRequest(BaseModel):
    team = models.ForeignKey("team.Team", related_name="team_join_requests", on_delete=models.CASCADE)
    chara = models.ForeignKey("chara.Chara", related_name="team_join_requests", on_delete=models.CASCADE)

    class Meta:
        unique_together = ('team', 'chara')
