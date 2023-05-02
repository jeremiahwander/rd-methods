"""Classes for exporting various metadata types."""

import json
from typing import List, Protocol


class IProvidePedigreeInfo(Protocol):  # pragma: no cover
    def get_subjects(self) -> List[str]:
        ...

    def get_family_id(self, subject_id: str) -> str:
        ...

    def get_paternal_id(self, subject_id: str) -> str:
        ...

    def get_maternal_id(self, subject_id: str) -> str:
        ...

    def get_sex(self, subject_id: str) -> str:
        ...

    def is_affected(self, subject_id: str) -> bool:
        ...


class PedigreeWriter:
    _pedigree_info: IProvidePedigreeInfo

    def __init__(
        self,
        pedigree_info: IProvidePedigreeInfo,
        families_to_write: List[str] | None = None,
    ) -> None:
        self._pedigree_info = pedigree_info
        self._families_to_write = families_to_write

    def _encode_sex(self, sex: str) -> str:
        if sex == "Male":
            return "1"
        elif sex == "Female":
            return "2"
        else:
            return "0"

    def _encode_affected(self, affected: bool) -> str:
        if affected:
            return "2"
        else:
            return "1"

    def _get_pedigree_line(self, subject: str) -> str:
        return (
            "\t".join(
                [
                    self._pedigree_info.get_family_id(subject),
                    subject,
                    self._pedigree_info.get_paternal_id(subject),
                    self._pedigree_info.get_maternal_id(subject),
                    self._encode_sex(self._pedigree_info.get_sex(subject)),
                    self._encode_affected(self._pedigree_info.is_affected(subject)),
                ]
            )
            + "\n"
        )

    def write(self, path: str) -> None:
        """Write a pedigree file to `path`."""
        with open(path, "w") as f:
            for subject in self._pedigree_info.get_subjects():
                if (
                    self._families_to_write is not None
                    and self._pedigree_info.get_family_id(subject) not in self._families_to_write
                ):
                    continue
                f.write(self._get_pedigree_line(subject))


class IProvideHpoInfo(Protocol):  # pragma: no cover
    def get_subjects(self) -> List[str]:
        ...

    def get_family_id(self, subject_id: str) -> str:
        ...

    def get_hpo_terms_present(self, subject_id: str) -> List[str]:
        ...


class HpoWriter:
    def __init__(
        self,
        hpo_info: IProvideHpoInfo,
        families_to_write: List[str] | None = None,
    ) -> None:
        self._hpo_info = hpo_info
        self._families_to_write = families_to_write

    def write(self, path: str) -> None:
        """Write an HPO file to `path`.

        The format of the output file should be as is expected by the AIP.

        "RGP_111_1":{
            "family_id":"RGP_111",
            "hpo_terms":[
                "HP:0012448",
                "HP:0012469",
                "HP:0000252"
            ]
        }
        """
        hpo_dict = {}

        for subject in self._hpo_info.get_subjects():
            if (
                self._families_to_write is not None
                and self._hpo_info.get_family_id(subject) not in self._families_to_write
            ):
                continue
            hpo_dict[subject] = {
                "family_id": self._hpo_info.get_family_id(subject),
                "hpo_terms": self._hpo_info.get_hpo_terms_present(subject),
            }

        with open(path, "w") as f:
            json.dump(hpo_dict, f, indent=4)
