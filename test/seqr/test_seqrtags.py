import pytest

from src.seqr.metadata import SeqrTags

TEST_FILEPATH = "test/data/valid_tags.tsv"


@pytest.fixture
def sample_tags():
    return SeqrTags.parse(TEST_FILEPATH)


def test_parse_noexist():
    with pytest.raises(FileNotFoundError):
        SeqrTags.parse("this/file/does/not/exist.tsv")


def test_parse_invalid():
    with pytest.raises(ValueError):
        SeqrTags.parse("test/data/invalid_tags.tsv")


def test_parse_success():
    SeqrTags.parse(TEST_FILEPATH)


def test_parse_multifile():
    # Note, no deduping will happen here. SeqrTags currently doesn't care about duplicate tag entries.
    SeqrTags.parse([TEST_FILEPATH, TEST_FILEPATH])


def test_get_highest_precedence_tag(sample_tags):
    # Get the highest precedence tag where there is only one tag for the family.
    assert sample_tags.get_highest_precedence_tag("single_tag") == "Known gene for phenotype"

    # Get the highest precedence tag where there are multiple tags for the family.
    assert sample_tags.get_highest_precedence_tag("multi_tag") == "Known gene for phenotype"

    # Get the highest precedence tag where there are multiple variants for the family.
    assert sample_tags.get_highest_precedence_tag("multi_var") == "Known gene for phenotype"

    # Get the highest precedence tag where there are multiple variants & multiple tags for the family.
    assert sample_tags.get_highest_precedence_tag("multi_both") == "Known gene for phenotype"

    # Get the highest precedence tag where there are no tags for the family.
    assert sample_tags.get_highest_precedence_tag("no_tag") is None

    # Get the highest precedence tag for a tag that's not in our precedence list.
    assert sample_tags.get_highest_precedence_tag("disinteresting") is None

    # Get the highest precedence tag where the family ID is not in the tags.
    assert sample_tags.get_highest_precedence_tag("not_in_tags") is None
