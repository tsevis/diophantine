"""BIP-39 recovery phrases and the secret derived from them.

A phrase is the only way back into an archive encrypted with one, so the
wordlist, the checksum and the derivation are all load-bearing: a single
changed word or a changed derivation locks the user out permanently.
"""

import base64

import pytest

from utils.recovery_phrase import (
    WordList,
    entropy_from_mnemonic,
    generate_recovery_phrase,
    legacy_secret_from_phrase,
    mnemonic_from_entropy,
    mnemonic_to_seed,
    phrase_secret_candidates,
    secret_from_phrase,
    validate_recovery_phrase,
)

WORDS = WordList.ENGLISH.value

# BIP-39 English test vectors, with the empty passphrase this app uses.
VECTORS = [
    (
        "00000000000000000000000000000000",
        ("abandon abandon abandon abandon abandon abandon abandon abandon "
         "abandon abandon abandon about"),
        ("5eb00bbddcf069084889a8ab9155568165f5c453ccb85e70811aaed6f6da5fc1"
         "9a5ac40b389cd370d086206dec8aa6c43daea6690f20ad3d8d48b2d2ce9e38e4"),
    ),
    (
        "7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f",
        ("legal winner thank year wave sausage worth useful legal winner "
         "thank yellow"),
        ("878386efb78845b3355bd15ea4d39ef97d179cb712b77d5c12b6be415fffeffe"
         "5f377ba02bf3f8544ab800b955e51fbff09828f682052a20faa6addbbddfb096"),
    ),
    (
        "80808080808080808080808080808080",
        ("letter advice cage absurd amount doctor acoustic avoid letter "
         "advice cage above"),
        ("77d6be9708c8218738934f84bbbb78a2e048ca007746cb764f0673e4b1812d17"
         "6bbb173e1a291f31cf633f1d0bad7d3cf071c30e98cd0688b5bcce65ecaceb36"),
    ),
]


def _words(mnemonic):
    return mnemonic.split() if isinstance(mnemonic, str) else list(mnemonic)


# ── The wordlist itself ──────────────────────────────────────────────


def test_the_wordlist_is_the_standard_two_thousand_and_forty_eight():
    assert len(WORDS) == 2048


def test_the_wordlist_has_no_duplicates():
    assert len(set(WORDS)) == 2048


def test_the_wordlist_is_in_the_order_the_standard_defines():
    """Index order is the encoding, so sorting is not cosmetic."""
    assert list(WORDS) == sorted(WORDS)


def test_the_wordlist_anchors_match_the_standard():
    assert WORDS[0] == "abandon"
    assert WORDS[3] == "about"
    assert WORDS[2047] == "zoo"


# ── Generation and validation ────────────────────────────────────────


@pytest.mark.parametrize(("entropy_hex", "expected", "_seed"), VECTORS)
def test_official_vectors_produce_the_expected_mnemonic(
        entropy_hex, expected, _seed):
    mnemonic = mnemonic_from_entropy(bytes.fromhex(entropy_hex))

    assert " ".join(_words(mnemonic)) == expected


@pytest.mark.parametrize(("entropy_hex", "mnemonic", "expected_seed"), VECTORS)
def test_official_vectors_produce_the_expected_seed(
        entropy_hex, mnemonic, expected_seed):
    assert mnemonic_to_seed(mnemonic.split()).hex() == expected_seed


@pytest.mark.parametrize(("entropy_hex", "mnemonic", "_seed"), VECTORS)
def test_entropy_survives_a_round_trip_through_the_mnemonic(
        entropy_hex, mnemonic, _seed):
    assert entropy_from_mnemonic(mnemonic.split()) == bytes.fromhex(entropy_hex)


@pytest.mark.parametrize(("strength", "expected_words"),
                         [(128, 12), (160, 15), (192, 18), (224, 21), (256, 24)])
def test_generated_phrases_have_the_length_their_strength_implies(
        strength, expected_words):
    words = _words(generate_recovery_phrase(strength))

    assert len(words) == expected_words
    assert validate_recovery_phrase(words)


def test_an_unsupported_strength_is_refused():
    with pytest.raises(ValueError, match="Strength must be"):
        generate_recovery_phrase(100)


def test_generated_phrases_differ_between_calls():
    phrases = {" ".join(_words(generate_recovery_phrase())) for _ in range(10)}

    assert len(phrases) == 10


def test_a_phrase_with_a_substituted_word_fails_its_checksum():
    words = ["abandon"] * 11 + ["about"]

    assert validate_recovery_phrase(words)
    assert not validate_recovery_phrase(["abandon"] * 11 + ["zoo"])


def test_a_phrase_with_a_word_outside_the_list_is_rejected():
    assert not validate_recovery_phrase(["abandon"] * 11 + ["notaword"])


def test_a_phrase_of_the_wrong_length_is_rejected():
    assert not validate_recovery_phrase(["abandon"] * 11)
    assert not validate_recovery_phrase([])


def test_transposing_two_words_of_a_known_phrase_is_caught():
    """A fixed phrase, because a checksum is only four bits for twelve words.

    Transposing words in a randomly generated phrase would pass validation
    roughly one time in sixteen, which is a flaky test rather than a weak
    checksum.
    """
    words = VECTORS[1][1].split()
    swapped = [words[1], words[0], *words[2:]]

    assert validate_recovery_phrase(words)
    assert not validate_recovery_phrase(swapped)


# ── The secret handed to the encryption tools ────────────────────────


def test_the_derived_secret_is_stable_for_a_given_phrase():
    words = ["abandon"] * 11 + ["about"]

    assert secret_from_phrase(words) == secret_from_phrase(words)


def test_different_phrases_derive_different_secrets():
    first = secret_from_phrase(["abandon"] * 11 + ["about"])
    second = secret_from_phrase(VECTORS[1][1].split())

    assert first != second


def test_the_derived_secret_does_not_leak_the_phrase():
    words = ["abandon"] * 11 + ["about"]

    secret = secret_from_phrase(words)

    assert "abandon" not in secret
    assert "about" not in secret


def test_the_derived_secret_is_a_single_line_within_veracrypts_limit():
    """VeraCrypt silently truncates past 64 characters."""
    secret = secret_from_phrase(["abandon"] * 11 + ["about"])

    assert secret.isascii()
    assert "\n" not in secret
    assert "\r" not in secret
    assert " " not in secret
    assert 0 < len(secret) <= 64


def test_the_derived_secret_is_built_from_the_stretched_seed():
    """It must be the PBKDF2 seed, not a bare hash of the words."""
    words = ["abandon"] * 11 + ["about"]

    expected = base64.urlsafe_b64encode(
        mnemonic_to_seed(words)[:32]).decode("ascii").rstrip("=")

    assert secret_from_phrase(words) == expected


def test_the_legacy_secret_is_the_phrase_as_older_versions_sent_it():
    words = ["abandon"] * 11 + ["about"]

    assert legacy_secret_from_phrase(words) == " ".join(words)


def test_candidates_try_the_derived_secret_before_the_legacy_one():
    words = ["abandon"] * 11 + ["about"]

    candidates = phrase_secret_candidates(words)

    assert candidates == (secret_from_phrase(words),
                          legacy_secret_from_phrase(words))
