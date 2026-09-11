import pytest

from utils.entropy import calculate_entropy, entropy_to_strength


def test_repeated_character_password_is_not_marked_strong():
    score = calculate_entropy("a" * 20)

    assert score == 0
    assert entropy_to_strength(score)[0] == "Very Weak"


def test_repeated_word_is_penalized_to_its_shortest_unit():
    assert calculate_entropy("passwordpasswordpassword") < 50


def test_an_empty_password_scores_nothing():
    assert calculate_entropy("") == 0


def test_an_ascending_sequence_is_not_credited_for_its_length():
    assert calculate_entropy("abcdefghijkl") == 0


def test_a_descending_sequence_is_caught_too():
    assert calculate_entropy("lkjihgfedcba") == 0


def test_a_short_run_is_not_mistaken_for_a_sequence():
    assert calculate_entropy("ab") > 0


def test_a_wider_character_set_scores_higher_at_equal_length():
    lower = calculate_entropy("abcdxyzwqrst")
    mixed = calculate_entropy("aBcdXyzW9r!t")

    assert mixed > lower


def test_a_longer_password_scores_higher_with_the_same_character_set():
    assert calculate_entropy("abcdxyzwqrstuvpo") > calculate_entropy("abcdxyzw")


@pytest.mark.parametrize(
    ("entropy", "expected"),
    [
        (0, "Very Weak"),
        (27.9, "Very Weak"),
        (28, "Weak"),
        (34.9, "Weak"),
        (35, "Fair"),
        (49.9, "Fair"),
        (50, "Good"),
        (64.9, "Good"),
        (65, "Strong"),
        (79.9, "Strong"),
        (80, "Very Strong"),
        (500, "Very Strong"),
    ],
)
def test_strength_bands_are_reported_at_their_boundaries(entropy, expected):
    label, colour = entropy_to_strength(entropy)

    assert label == expected
    assert colour


def test_the_warning_threshold_the_ui_uses_sits_inside_fair():
    """encrypt_tab warns below 50, which must line up with a band edge."""
    assert entropy_to_strength(49.9)[0] == "Fair"
    assert entropy_to_strength(50)[0] == "Good"
