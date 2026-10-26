from django.contrib import admin

from .models import Guess, GameSession


class GuessInline(admin.TabularInline):
    model = Guess
    extra = 0
    readonly_fields = ("value", "result", "created_at")
    can_delete = False


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "attempts_used", "points", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username",)
    inlines = [GuessInline]
