from controllers.check_rate_limit import RATE_LIMIT_LOGIN_ATTEMPTS as MAX_ATTEMPTS
from controllers.check_rate_limit import Ratelimit


def fail_login(limiter, username, times):
    for _ in range(times):
        limiter.increment_login_attempt(username)


def test_new_user_is_allowed():
    assert Ratelimit().check_rate_limit("bob") is True


def test_allows_while_below_max_attempts():
    limiter = Ratelimit()

    fail_login(limiter, "bob", MAX_ATTEMPTS - 1)

    assert limiter.check_rate_limit("bob") is True


def test_blocks_at_max_attempts():
    limiter = Ratelimit()

    fail_login(limiter, "bob", MAX_ATTEMPTS)

    assert limiter.check_rate_limit("bob") is False


def test_check_does_not_count_as_attempt():
    limiter = Ratelimit()
    fail_login(limiter, "bob", MAX_ATTEMPTS - 1)

    for _ in range(10):
        limiter.check_rate_limit("bob")

    assert limiter.check_rate_limit("bob") is True


def test_attempts_are_counted_per_username():
    limiter = Ratelimit()

    fail_login(limiter, "bob", MAX_ATTEMPTS)

    assert limiter.check_rate_limit("alice") is True


def test_reset_attempts_unblocks():
    limiter = Ratelimit()
    fail_login(limiter, "bob", MAX_ATTEMPTS)

    limiter.reset_attempts("bob")

    assert limiter.check_rate_limit("bob") is True


def test_increment_records_attempt_time(clock):
    limiter = Ratelimit()

    limiter.increment_login_attempt("bob")

    assert limiter.login_attempts["bob"] == {"attempts": 1, "last_attempt_time": clock.now}


def test_still_blocked_before_cooldown(clock):
    limiter = Ratelimit()
    fail_login(limiter, "bob", MAX_ATTEMPTS)

    clock.advance(59)

    assert limiter.check_rate_limit("bob") is False


def test_unblocked_after_cooldown(clock):
    limiter = Ratelimit()
    fail_login(limiter, "bob", MAX_ATTEMPTS)

    clock.advance(61)

    assert limiter.check_rate_limit("bob") is True
    assert limiter.login_attempts["bob"]["attempts"] == 0
