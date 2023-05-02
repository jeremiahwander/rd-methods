import pytest

from lib.seqr.metadata import SeqrTags

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


def test_get_families(sample_tags):
    # Get all families.
    assert sample_tags.get_families() == [
        "single_tag",
        "multi_tag",
        "multi_var",
        "multi_both",
        "no_tag",
        "disinteresting",
    ]


def test_get_variants_for_family(sample_tags):
    # Get the variants for a family with a single variant.
    assert sample_tags.get_variants_for_family("single_tag") == ["1-1-A-T"]

    # Get the variants for a family with multiple variants.
    assert sample_tags.get_variants_for_family("multi_var") == ["1-1-A-T", "1-2-C-G"]

    # Get the variants for a family with no variants.
    assert sample_tags.get_variants_for_family("not_in_tags") == []


def test_get_tags_for_family_and_variant(sample_tags):
    # Get the tags for a family with a single variant.
    assert sample_tags.get_tags_for_family_and_variant("single_tag", "1-1-A-T") == ["Known gene for phenotype"]

    # Get the tags for a family with multiple tags for a single variant.
    assert sample_tags.get_tags_for_family_and_variant("multi_tag", "1-1-A-T") == [
        "Known gene for phenotype",
        "Tier 1 - Novel gene and phenotype",
    ]

    # Get tags for a family/variant with no tags assigned.
    assert sample_tags.get_tags_for_family_and_variant("no_tag", "1-1-A-T") == []

    # Get the tags for a family with no variants.
    with pytest.raises(ValueError):
        sample_tags.get_tags_for_family_and_variant("not_in_tags", "1-1-A-T")
