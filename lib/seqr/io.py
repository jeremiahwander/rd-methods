"""Classes for exporting various metadata types."""

import json
from collections import defaultdict
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

    def _encode_parent(self, parent: str) -> str:
        if parent:
            return parent
        return "0"

    def _get_pedigree_line(self, subject: str) -> str:
        return (
            "\t".join(
                [
                    self._pedigree_info.get_family_id(subject),
                    subject,
                    self._encode_parent(self._pedigree_info.get_paternal_id(subject)),
                    self._encode_parent(self._pedigree_info.get_maternal_id(subject)),
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


class IProvideTagInfo(Protocol):
    def get_families(self) -> List[str]:
        ...

    def get_variants_for_family(self, family_id: str) -> List[str]:
        ...

    def get_tags_for_family_and_variant(self, family_id: str, variant_id: str) -> List[str]:
        ...


class ExternalLabelWriter:
    def __init__(
        self,
        tag_info: IProvideTagInfo,
        families_to_write: List[str] | None = None,
        tags_to_write: List[str] | None = None,
    ) -> None:
        self._tag_info = tag_info
        self._families_to_write = families_to_write
        self._tags_to_write = tags_to_write

    def write(self, path: str) -> None:
        """Write an External Label file to `path`.

        The format of the output file should be as is expected by the AIP.

        "RGP_111_3": {
            "19-41970476-A-T": [
                "Known gene for phenotype"
            ]
        },
        """
        tag_dict: dict[str, dict[str, List[str]]] = defaultdict(dict)

        for family in self._tag_info.get_families():
            if self._families_to_write is not None and family not in self._families_to_write:
                continue
            for variant in self._tag_info.get_variants_for_family(family):
                tags = self._tag_info.get_tags_for_family_and_variant(family, variant)
                if self._tags_to_write is not None:
                    tags = [tag for tag in tags if tag in self._tags_to_write]
                if tags:
                    tag_dict[family][variant] = tags

        with open(path, "w") as f:
            json.dump(tag_dict, f, indent=4)
