import pandas as pd
import pytest

from lib.seqr.io import PedigreeWriter
from lib.seqr.metadata import SeqrSubjects

TEST_FILEPATH = "test/data/valid_subjects.tsv"


@pytest.fixture
def sample_subjects():
    return SeqrSubjects.parse(TEST_FILEPATH)


@pytest.fixture(scope="session")
def output_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "out.fam"


def test_write(sample_subjects, output_file):
    PedigreeWriter(sample_subjects).write(output_file)

    out_df = pd.read_csv(
        output_file,
        sep="\t",
        header=None,
        names=["family_id", "subject_id", "paternal_id", "maternal_id", "sex", "affected"],
    )

    test_df = (
        pd.read_csv(TEST_FILEPATH, sep="\t")
        .rename(
            columns={
                "Family ID": "family_id",
                "Individual ID": "subject_id",
                "Paternal ID": "paternal_id",
                "Maternal ID": "maternal_id",
                "Sex": "sex",
                "Affected Status": "affected",
            }
        )
        .drop(columns=["Notes", "Individual Data Loaded", "HPO Terms (present)", "HPO Terms (absent)"])
        .fillna("0")
    )

    test_df.sex = test_df.sex.map({"Male": 1, "Female": 2, "Unknown": 0})
    test_df.affected = test_df.affected.map({"Affected": 2, "Unaffected": 1})

    pd.testing.assert_frame_equal(out_df, test_df)


def test_write_with_families(sample_subjects, output_file):
    families = ["RGP_123"]
    PedigreeWriter(sample_subjects, families_to_write=families).write(output_file)

    out_df = pd.read_csv(
        output_file,
        sep="\t",
        header=None,
        names=["family_id", "subject_id", "paternal_id", "maternal_id", "sex", "affected"],
    )

    test_df = (
        pd.read_csv(TEST_FILEPATH, sep="\t")
        .rename(
            columns={
                "Family ID": "family_id",
                "Individual ID": "subject_id",
                "Paternal ID": "paternal_id",
                "Maternal ID": "maternal_id",
                "Sex": "sex",
                "Affected Status": "affected",
            }
        )
        .drop(columns=["Notes", "Individual Data Loaded", "HPO Terms (present)", "HPO Terms (absent)"])
        .fillna("0")
        .loc[lambda df: df.family_id.isin(families)]
    )

    test_df.sex = test_df.sex.map({"Male": 1, "Female": 2})
    test_df.affected = test_df.affected.map({"Affected": 2, "Unaffected": 1})

    pd.testing.assert_frame_equal(out_df, test_df)
