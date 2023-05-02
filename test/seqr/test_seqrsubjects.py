import pytest

from lib.seqr.metadata import SeqrSubjects

TEST_FILEPATH = "test/data/valid_subjects.tsv"


@pytest.fixture
def sample_subjects():
    return SeqrSubjects.parse(TEST_FILEPATH)


def test_parse_noexist():
    with pytest.raises(FileNotFoundError):
        SeqrSubjects.parse("this/file/does/not/exist.tsv")


def test_parse_invalid():
    with pytest.raises(ValueError):
        SeqrSubjects.parse("test/data/invalid_subjects.tsv")


def test_parse_success():
    SeqrSubjects.parse(TEST_FILEPATH)


def test_parse_multifile():
    # Note we should get a deduping warning here.
    SeqrSubjects.parse([TEST_FILEPATH, TEST_FILEPATH])


def test_get_subjects(sample_subjects):
    assert set(sample_subjects.get_subjects()) == {"RGP_123_1", "RGP_123_2", "RGP_123_3", "RGP_321_1", "RGP_321_2"}


def test_get_families(sample_subjects):
    assert set(sample_subjects.get_families()) == {"RGP_123", "RGP_321"}


def test_get_subjects_for_family(sample_subjects):
    assert set(sample_subjects.get_subjects_for_family("RGP_123")) == {"RGP_123_1", "RGP_123_2", "RGP_123_3"}
    with pytest.raises(ValueError):
        sample_subjects.get_subjects_for_family("RGP_XYZ")


def test_remove_subject(sample_subjects):
    sample_subjects.remove_subject("RGP_123_1")
    assert set(sample_subjects.get_subjects()) == {"RGP_123_2", "RGP_123_3", "RGP_321_1", "RGP_321_2"}
    with pytest.raises(ValueError):
        sample_subjects.remove_subject("RGP_XYZ_Q")


def test_remove_family(sample_subjects):
    sample_subjects.remove_family("RGP_123")
    assert sample_subjects.get_families() == ["RGP_321"]
    with pytest.raises(ValueError):
        sample_subjects.remove_family("RGP_XYZ")


def test_is_data_loaded(sample_subjects):
    assert sample_subjects.is_data_loaded("RGP_123_1") is True
    assert sample_subjects.is_data_loaded("RGP_321_2") is False
    with pytest.raises(ValueError):
        sample_subjects.is_data_loaded("RGP_XYZ_Q")


def test_is_affected(sample_subjects):
    assert sample_subjects.is_affected("RGP_123_1") is False
    assert sample_subjects.is_affected("RGP_123_3") is True
    with pytest.raises(ValueError):
        sample_subjects.is_affected("RGP_XYZ_Q")
