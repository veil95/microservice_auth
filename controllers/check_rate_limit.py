from time import time
from datetime import timedelta

RATE_LIMIT_LOGIN_COOLDOWN_S = timedelta(minutes=1).total_seconds()


class Ratelimit:
    def __init__(self):
        self.login_attempts = {}

    def check_rate_limit(self, username: str) -> bool:
        current_time = time()

        if username not in self.login_attempts:
            self.login_attempts[username] = {"attempts": 0, "last_attempt_time": current_time}
            return True

        user_attempts = self.login_attempts[username]
        if current_time - user_attempts["last_attempt_time"] > RATE_LIMIT_LOGIN_COOLDOWN_S:
            user_attempts["attempts"] = 0
            user_attempts["last_attempt_time"] = current_time
            return True

        if user_attempts["attempts"] <= 5:
            return True
        return False

    def increment_login_attempt(self, username: str):
        if username not in self.login_attempts:
            self.login_attempts[username] = {"attempts": 1, "last_attempt_time": time()}
        else:
            self.login_attempts[username]["attempts"] += 1
            self.login_attempts[username]["last_attempt_time"] = time()

    def reset_attempts(self, username: str):
        self.login_attempts[username]["attempts"] = 0
        return


