"""Trying more than one secret against the same encrypted input."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

Result = TypeVar("Result")


def attempt_with_secrets(
        action: Callable[[str], Result],
        secrets: Sequence[str]) -> Result:
    """Run ``action`` against each secret and return the first success.

    A recovery phrase has more than one plausible secret behind it: the
    derived one written today and the bare phrase older archives used.  Only
    the archive can say which applies, so the caller offers both in the order
    it considers most likely.

    The error raised is the first one, because the first secret is the one
    that describes the expected case; a later failure is only interesting
    when the earlier one already failed for the same reason.
    """
    if not secrets:
        raise ValueError("At least one secret is required.")

    first_error: Exception | None = None
    for secret in secrets:
        try:
            return action(secret)
        except Exception as error:  # noqa: BLE001 - the next secret may work
            if first_error is None:
                first_error = error
    raise first_error
