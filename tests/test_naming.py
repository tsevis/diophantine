"""Output naming schemes.

These decide the filename a user finds on disk after an encryption run, so a
change here silently renames everyone's output.
"""

import re

from utils.naming import chronos_name, numeric_name, original_name


def test_original_name_keeps_the_source_name_and_appends_the_extension():
    assert original_name("/tmp/report.pdf", ext=".gpg") == "report.pdf.gpg"


def test_original_name_of_a_directory_ignores_a_trailing_separator():
    assert original_name("/tmp/papers/", ext=".7z") == "papers.7z"


def test_original_name_defaults_to_zip():
    assert original_name("/tmp/notes.txt") == "notes.txt.zip"


def test_numeric_name_is_zero_padded_to_three_digits():
    assert numeric_name(3, ext=".7z") == "003.7z"
    assert numeric_name(42) == "042.zip"


def test_numeric_name_does_not_truncate_beyond_the_padding():
    assert numeric_name(1234, ext=".gpg") == "1234.gpg"


def test_chronos_name_prefixes_todays_local_date():
    name = chronos_name(7, ext=".7z")

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}_007\.7z", name), name


def test_every_scheme_produces_distinct_names_for_distinct_indices():
    names = {numeric_name(index) for index in range(1, 20)}
    assert len(names) == 19

    names = {chronos_name(index) for index in range(1, 20)}
    assert len(names) == 19
