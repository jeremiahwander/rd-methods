import json

import pytest

from lib.seqr.io import ExternalLabelWriter
from lib.seqr.metadata import SeqrTags

TEST_FILEPATH = "test/data/valid_tags.tsv"


@pytest.fixture
def sample_tags():
    return SeqrTags.parse(TEST_FILEPATH)


@pytest.fixture(scope="session")
def output_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "out.fam"


def test_write(sample_tags, output_file):
    def get_unique_tags_for_family(family):
        return list(
            {
                t
                for variant in sample_tags.get_variants_for_family(family)
                for t in sample_tags.get_tags_for_family_and_variant(family, variant)
            }
        )

    ExternalLabelWriter(sample_tags).write(output_file)

    with open(output_file, "r") as f:
        out_json = json.load(f)

    for family in sample_tags.get_families():
        if not get_unique_tags_for_family(family):
            assert family not in out_json
            continue
        assert family in out_json
        for variant in sample_tags.get_variants_for_family(family):
            truth_tags = sample_tags.get_tags_for_family_and_variant(family, variant)
            if not truth_tags:
                continue
            assert variant in out_json[family]
            assert out_json[family][variant] == truth_tags


def test_write_with_families(sample_tags, output_file):
    families = sample_tags.get_families()[0:2]
    ExternalLabelWriter(sample_tags, families_to_write=families).write(output_file)

    with open(output_file, "r") as f:
        out_json = json.load(f)

    for family in sample_tags.get_families():
        if family not in families:
            assert family not in out_json
            continue
        assert family in out_json
        for variant in sample_tags.get_variants_for_family(family):
            truth_tags = sample_tags.get_tags_for_family_and_variant(family, variant)
            if not truth_tags:
                continue
            assert variant in out_json[family]
            assert out_json[family][variant] == truth_tags


def test_write_with_tags(sample_tags, output_file):
    tags = ["Tier 1 - Novel gene and phenotype", "Tier 2 - Known gene, new phenotype"]
    ExternalLabelWriter(sample_tags, tags_to_write=tags).write(output_file)

    with open(output_file, "r") as f:
        out_json = json.load(f)

    # Tricky test logic here:
    # - If a family has no variants with a tag from `tags`, that family shouldn't be in the output.
    #       Per the test file used above, single_tag, no_tag, and disinteresting should all be missing from the output.
    # - Only variants with one or more of the tags from tags should be included in the output.
    #       Per the test file used above, multi_var:1-1-A-T should be missing from the output.
    for family in sample_tags.get_families():
        family_has_tag = any(
            tag in tags
            for variant in sample_tags.get_variants_for_family(family)
            for tag in sample_tags.get_tags_for_family_and_variant(family, variant)
        )
        if not family_has_tag:
            assert family not in out_json
            continue
        for variant in sample_tags.get_variants_for_family(family):
            variant_has_tag = any(tag in tags for tag in sample_tags.get_tags_for_family_and_variant(family, variant))
            if not variant_has_tag:
                assert variant not in out_json[family]
                continue
            for tag in sample_tags.get_tags_for_family_and_variant(family, variant):
                if tag in tags:
                    assert tag in out_json[family][variant]
                else:
                    assert tag not in out_json[family][variant]
