from utils.entropy import calculate_entropy, entropy_to_strength


def test_repeated_character_password_is_not_marked_strong():
    score = calculate_entropy("a" * 20)

    assert score == 0
    assert entropy_to_strength(score)[0] == "Very Weak"


def test_repeated_word_is_penalized_to_its_shortest_unit():
    assert calculate_entropy("passwordpasswordpassword") < 50
