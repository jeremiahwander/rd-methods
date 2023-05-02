import logging
from typing import List, Optional

import pandas as pd

# An ordered list of tags of interest for grouping families.
TAGS_OF_INTEREST = [
    "Known gene for phenotype",
    "Tier 1 - Novel gene and phenotype",
    "Tier 1 - Novel gene for known phenotype",
    "Tier 1 - Phenotype expansion",
    "Tier 1 - Novel mode of inheritance",
    "Tier 1 - Known gene, new phenotype",
    "Tier 2 - Novel gene and phenotype",
    "Tier 2 - Novel gene for known phenotype",
    "Tier 2 - Phenotype expansion",
    "Tier 2 - Phenotype not delineated",
    "Tier 2 - Known gene, new phenotype",
]


class SeqrTags:
    df: pd.DataFrame

    def __init__(self, df: pd.DataFrame) -> None:
        self._validate_input_df(df)
        self.df = df

    def _validate_input_df(self, df: pd.DataFrame) -> None:
        for col in ["family", "tags"]:
            if col not in df.columns:
                raise ValueError(f"Input dataframe must contain column '{col}'.")

    @classmethod
    def parse(cls, tag_paths: str | List[str]) -> "SeqrTags":
        """Parse one or more tag exports from seqr. Return a SeqrTags object."""
        if isinstance(tag_paths, str):
            tag_paths = [tag_paths]
        full_df = pd.DataFrame()
        for path in tag_paths:
            df = pd.read_csv(path, sep="\t")
            full_df = pd.concat([full_df, df], ignore_index=True) if not full_df.empty else df
        return SeqrTags(full_df)

    def get_highest_precedence_tag(self, family_id: str) -> Optional[str]:
        """Get the highest precedence tag for a given family ID.

        If `family_id` is not found in the tags, return None.
        """
        if family_id not in self.df["family"].values:
            return None

        tags = self._get_tags_for_family(family_id)
        if not tags:
            return None

        for tag in TAGS_OF_INTEREST:
            if tag in tags:
                return tag

        return None

    def _get_tags_for_family(self, family_id: str) -> List[str]:
        """Get all tags for a given family ID."""
        variants = self.df[self.df["family"] == family_id]
        tags = set()
        for _, row in variants.iterrows():
            if pd.isna(row["tags"]):
                continue
            tags.update(row["tags"].split("|"))
        return list(tags)


class SeqrSubjects:
    def __init__(self, df: pd.DataFrame) -> None:
        self._validate_input_df(df)
        self.df = df

    def _validate_input_df(self, df: pd.DataFrame) -> None:
        for col in [
            "Family ID",
            "Individual ID",
            "Paternal ID",
            "Maternal ID",
            "Sex",
            "Affected Status",
            "Individual Data Loaded",
            "HPO Terms (present)",
        ]:
            if col not in df.columns:
                raise ValueError(f"Input dataframe must contain column '{col}'.")

    @classmethod
    def parse(cls, subject_paths: str | List[str]) -> "SeqrSubjects":
        """Parse one or more subject exports from seqr. Return a SeqrSubjects object."""
        if isinstance(subject_paths, str):
            subject_paths = [subject_paths]
        full_df = pd.DataFrame()
        for path in subject_paths:
            df = pd.read_csv(path, sep="\t")
            full_df = pd.concat([full_df, df], ignore_index=True) if not full_df.empty else df

        # Drop duplicates, issue a warning if any are found.
        if full_df.duplicated(subset=["Individual ID"]).any():
            logging.warning("Duplicate subject IDs found in input files. Duplicates will be removed.")
            full_df.drop_duplicates(subset=["Individual ID"], inplace=True)

        return SeqrSubjects(full_df)

    def get_subjects(self) -> List[str]:
        """Return a list of all subject IDs."""
        return self.df["Individual ID"].values.tolist()

    def get_families(self) -> List[str]:
        """Return a list of all family IDs."""
        return self.df["Family ID"].unique().tolist()

    def get_subjects_for_family(self, family_id: str) -> List[str]:
        """Return a list of all subject IDs for a given family ID."""
        if family_id not in self.get_families():
            raise ValueError(f"Family ID '{family_id}' not found.")
        return self.df[self.df["Family ID"] == family_id]["Individual ID"].values.tolist()

    def remove_subject(self, subject_id: str) -> None:
        """Remove a subject."""
        if subject_id not in self.get_subjects():
            raise ValueError(f"Subject ID '{subject_id}' not found.")
        self.df = self.df[self.df["Individual ID"] != subject_id]

    def remove_family(self, family_id: str) -> None:
        """Remove a family."""
        if family_id not in self.get_families():
            raise ValueError(f"Family ID '{family_id}' not found.")
        self.df = self.df[self.df["Family ID"] != family_id]

    def _get_string_field(self, subject_id: str, field: str) -> str:
        """Return a string field for a given subject ID.

        If the value for the field is missing, return an empty string.
        """
        if subject_id not in self.get_subjects():
            raise ValueError(f"Subject ID '{subject_id}' not found.")
        value = self.df[self.df["Individual ID"] == subject_id][field].values[0]
        return "" if pd.isna(value) else value

    def is_affected(self, subject_id: str) -> bool:
        """Return whether or not a subject is affected."""
        return self._get_string_field(subject_id, "Affected Status") == "Affected"

    def get_sex(self, subject_id: str) -> str:
        """Return the sex of a subject."""
        return self._get_string_field(subject_id, "Sex")

    def get_family_id(self, subject_id: str) -> str:
        """Return the family ID of a subject."""
        return self._get_string_field(subject_id, "Family ID")

    def get_paternal_id(self, subject_id: str) -> str:
        """Return the paternal ID of a subject. If no paternal ID is present, return an empty string."""
        return self._get_string_field(subject_id, "Paternal ID")

    def get_maternal_id(self, subject_id: str) -> str:
        """Return the maternal ID of a subject. If no maternal ID is present, an empty string."""
        return self._get_string_field(subject_id, "Maternal ID")

    def is_data_loaded(self, subject_id: str) -> bool:
        """Return whether or not data are loaded for a given subject ID."""
        return self._get_string_field(subject_id, "Individual Data Loaded") == "Yes"

    def _parse_hpo_terms(self, hpo_terms: str) -> List[str]:
        """Parse HPO terms from a string."""
        if pd.isna(hpo_terms) or not hpo_terms:
            return []
        return [term.split("(")[0].strip() for term in hpo_terms.split("|")]

    def get_hpo_terms_present(self, subject_id: str) -> List[str]:
        """Return the list of HPO terms present for a given subject ID."""
        return self._parse_hpo_terms(self._get_string_field(subject_id, "HPO Terms (present)"))
