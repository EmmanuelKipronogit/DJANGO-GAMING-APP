from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Count, Max, Min, Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import logic
from .forms import GuessForm, SignUpForm
from .models import Guess, GameSession


def home(request):
    if request.user.is_authenticated:
        return redirect("play")
    return render(request, "game/home.html", {"max_attempts": logic.MAX_ATTEMPTS})


def signup(request):
    if request.user.is_authenticated:
        return redirect("play")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome, {user.username}! Ready to play?")
        return redirect("play")
    return render(request, "registration/signup.html", {"form": form})


@login_required
def play(request):
    game = request.user.games.filter(status=GameSession.ACTIVE).first()
    recent = request.user.games.exclude(status=GameSession.ACTIVE)[:5]
    last = request.user.games.exclude(status=GameSession.ACTIVE).first()
    context = {
        "game": game,
        "form": GuessForm(),
        "recent": recent,
        "max_attempts": logic.MAX_ATTEMPTS,
        "min_number": logic.MIN_NUMBER,
        "max_number": logic.MAX_NUMBER,
    }
    # Reveal the number only for the game that just ended.
    if game is None and last is not None and request.session.pop("show_last", None) == last.pk:
        context["just_finished"] = last
    return render(request, "game/play.html", context)


@login_required
@require_POST
def new_game(request):
    try:
        with transaction.atomic():
            GameSession.objects.get_or_create(
                user=request.user,
                status=GameSession.ACTIVE,
                defaults={"secret": logic.new_secret()},
            )
    except IntegrityError:
        pass  # double-click race: the active game already exists
    return redirect("play")


@login_required
@require_POST
def guess(request):
    form = GuessForm(request.POST)
    if not form.is_valid():
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
        return redirect("play")

    value = form.cleaned_data["guess"]
    with transaction.atomic():
        # Lock the row so two rapid requests can't both count as the last attempt.
        game = (
            GameSession.objects.select_for_update()
            .filter(user=request.user, status=GameSession.ACTIVE)
            .first()
        )
        if game is None:
            messages.info(request, "Start a new game first.")
            return redirect("play")

        result = logic.check_guess(game.secret, value)
        Guess.objects.create(game=game, value=value, result=result)
        game.attempts_used += 1

        if result == "correct":
            game.status = GameSession.WON
            game.points = logic.points_for_win(game.attempts_used)
            game.finished_at = timezone.now()
            messages.success(
                request,
                f"Correct! {game.secret} was the number. You scored {game.points} points "
                f"in {game.attempts_used} guess{'es' if game.attempts_used != 1 else ''}.",
            )
            request.session["show_last"] = game.pk
        elif game.attempts_used >= logic.MAX_ATTEMPTS:
            game.status = GameSession.LOST
            game.finished_at = timezone.now()
            messages.error(request, f"Out of guesses. The number was {game.secret}.")
            request.session["show_last"] = game.pk
        else:
            hint = "higher" if result == "higher" else "lower"
            messages.info(request, f"{value} is too {'low' if hint == 'higher' else 'high'}. Go {hint}!")
        game.save()
    return redirect("play")


def leaderboard(request):
    rows = (
        GameSession.objects.filter(status__in=[GameSession.WON, GameSession.LOST])
        .values("user__username")
        .annotate(
            wins=Count("id", filter=Q(status=GameSession.WON)),
            played=Count("id"),
            total_points=Sum("points"),
            best=Min("attempts_used", filter=Q(status=GameSession.WON)),
            last_played=Max("finished_at"),
        )
        .order_by("-total_points", "-wins", "last_played")[:20]
    )
    return render(request, "game/leaderboard.html", {"rows": rows})
