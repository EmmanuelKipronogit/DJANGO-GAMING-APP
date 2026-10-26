from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from . import logic
from .models import GameSession


class LogicTests(TestCase):
    def test_check_guess(self):
        self.assertEqual(logic.check_guess(50, 50), "correct")
        self.assertEqual(logic.check_guess(50, 10), "higher")
        self.assertEqual(logic.check_guess(50, 90), "lower")

    def test_secret_in_range(self):
        for _ in range(500):
            self.assertTrue(logic.MIN_NUMBER <= logic.new_secret() <= logic.MAX_NUMBER)

    def test_points(self):
        self.assertEqual(logic.points_for_win(1), 70)
        self.assertEqual(logic.points_for_win(7), 10)


class DatabaseTests(TestCase):
    def test_running_on_postgres(self):
        self.assertEqual(connection.vendor, "postgresql")


class FlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ana", password="s3cret-pass-99")

    def login(self):
        self.client.login(username="ana", password="s3cret-pass-99")

    def start(self, secret=42):
        self.login()
        self.client.post(reverse("new_game"))
        game = GameSession.objects.get(user=self.user, status="active")
        game.secret = secret
        game.save()
        return game

    def test_signup_logs_in(self):
        resp = self.client.post(
            reverse("signup"),
            {"username": "newbie", "password1": "tr0ub4dor-xyz", "password2": "tr0ub4dor-xyz"},
        )
        self.assertRedirects(resp, reverse("play"))
        self.assertTrue(User.objects.filter(username="newbie").exists())

    def test_play_requires_login(self):
        resp = self.client.get(reverse("play"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp.url)

    def test_only_one_active_game(self):
        self.login()
        self.client.post(reverse("new_game"))
        self.client.post(reverse("new_game"))
        self.assertEqual(GameSession.objects.filter(user=self.user, status="active").count(), 1)

    def test_win(self):
        game = self.start(42)
        self.client.post(reverse("guess"), {"guess": 10})
        self.client.post(reverse("guess"), {"guess": 42})
        game.refresh_from_db()
        self.assertEqual(game.status, "won")
        self.assertEqual(game.attempts_used, 2)
        self.assertEqual(game.points, logic.points_for_win(2))

    def test_loss_after_max_attempts(self):
        game = self.start(42)
        for _ in range(logic.MAX_ATTEMPTS):
            self.client.post(reverse("guess"), {"guess": 1})
        game.refresh_from_db()
        self.assertEqual(game.status, "lost")
        self.assertEqual(game.points, 0)

    def test_invalid_guess_not_counted(self):
        game = self.start(42)
        for bad in ("0", "101", "abc", ""):
            self.client.post(reverse("guess"), {"guess": bad})
        game.refresh_from_db()
        self.assertEqual(game.attempts_used, 0)

    def test_secret_never_in_page_while_playing(self):
        self.start(77)
        html = self.client.get(reverse("play")).content.decode()
        self.assertNotIn("77", html.replace("100", ""))  # 100 is the range upper bound

    def test_cannot_guess_after_game_over(self):
        game = self.start(42)
        self.client.post(reverse("guess"), {"guess": 42})
        self.client.post(reverse("guess"), {"guess": 5})
        game.refresh_from_db()
        self.assertEqual(game.attempts_used, 1)

    def test_users_cannot_touch_each_others_games(self):
        other = User.objects.create_user("bob", password="s3cret-pass-99")
        GameSession.objects.create(user=other, secret=5)
        self.start(42)
        self.client.post(reverse("guess"), {"guess": 5})
        self.assertEqual(GameSession.objects.get(user=other).attempts_used, 0)

    def test_leaderboard_ranks_by_points(self):
        bob = User.objects.create_user("bob", password="s3cret-pass-99")
        GameSession.objects.create(user=self.user, secret=1, status="won", attempts_used=5, points=30)
        GameSession.objects.create(user=bob, secret=1, status="won", attempts_used=1, points=70)
        html = self.client.get(reverse("leaderboard")).content.decode()
        self.assertLess(html.index("bob"), html.index("ana"))

    def test_logout_requires_post(self):
        self.login()
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.client.post(reverse("logout"))
        self.assertEqual(self.client.get(reverse("play")).status_code, 302)
