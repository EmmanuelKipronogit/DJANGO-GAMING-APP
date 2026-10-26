from django.conf import settings
from django.db import models

from . import logic


class GameSession(models.Model):
    ACTIVE, WON, LOST = "active", "won", "lost"
    STATUS_CHOICES = [(ACTIVE, "In progress"), (WON, "Won"), (LOST, "Lost")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="games")
    secret = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ACTIVE)
    attempts_used = models.PositiveSmallIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status"])]
        constraints = [
            # A player can only ever have one game in progress.
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(status="active"),
                name="one_active_game_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.status} ({self.attempts_used} guesses)"

    @property
    def attempts_left(self):
        return logic.MAX_ATTEMPTS - self.attempts_used

    @property
    def is_active(self):
        return self.status == self.ACTIVE


class Guess(models.Model):
    game = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name="guesses")
    value = models.PositiveSmallIntegerField()
    result = models.CharField(max_length=10)  # correct / higher / lower
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
