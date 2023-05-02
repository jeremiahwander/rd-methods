import json

import pytest

from lib.seqr.io import HpoWriter
from lib.seqr.metadata import SeqrSubjects

TEST_FILEPATH = "test/data/valid_subjects.tsv"


@pytest.fixture
def sample_subjects():
    return SeqrSubjects.parse(TEST_FILEPATH)


@pytest.fixture(scope="session")
def output_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "out.fam"


def test_write(sample_subjects, output_file):
    HpoWriter(sample_subjects).write(output_file)

    with open(output_file, "r") as f:
        out_json = json.load(f)

    for subject in sample_subjects.get_subjects():
        assert subject in out_json
        assert out_json[subject]["family_id"] == sample_subjects.get_family_id(subject)
        assert out_json[subject]["hpo_terms"] == sample_subjects.get_hpo_terms_present(subject)


def test_write_with_families(sample_subjects, output_file):
    families = ["RGP_123"]
    HpoWriter(sample_subjects, families_to_write=families).write(output_file)

    with open(output_file, "r") as f:
        out_json = json.load(f)

    for subject in sample_subjects.get_subjects():
        if sample_subjects.get_family_id(subject) not in families:
            assert subject not in out_json
            continue
        assert subject in out_json
        assert out_json[subject]["family_id"] == sample_subjects.get_family_id(subject)
        assert out_json[subject]["hpo_terms"] == sample_subjects.get_hpo_terms_present(subject)
