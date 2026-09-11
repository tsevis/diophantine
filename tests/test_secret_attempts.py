"""Trying more than one secret against the same encrypted input."""

import pytest

from utils.secret_attempts import attempt_with_secrets


def test_the_first_secret_that_works_ends_the_attempt():
    tried = []

    def action(secret):
        tried.append(secret)
        if secret != "right":
            raise RuntimeError("wrong password")

    attempt_with_secrets(action, ("right", "unused"))

    assert tried == ["right"]


def test_a_later_secret_is_tried_after_an_earlier_one_fails():
    tried = []

    def action(secret):
        tried.append(secret)
        if secret != "legacy":
            raise RuntimeError("wrong password")

    attempt_with_secrets(action, ("derived", "legacy"))

    assert tried == ["derived", "legacy"]


def test_the_failure_from_the_first_secret_is_what_surfaces():
    """The derived secret is the one today's archives use, so its error is
    the one that describes the likely problem."""
    def action(secret):
        raise RuntimeError(f"failed for {secret}")

    with pytest.raises(RuntimeError, match="failed for derived"):
        attempt_with_secrets(action, ("derived", "legacy"))


def test_an_empty_list_of_secrets_is_a_programming_error():
    with pytest.raises(ValueError, match="At least one secret"):
        attempt_with_secrets(lambda secret: None, ())


def test_the_return_value_of_the_successful_action_is_passed_through():
    assert attempt_with_secrets(lambda secret: f"ok:{secret}", ("one",)) == "ok:one"
