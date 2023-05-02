#!/usr/bin/env python3

"""This python script generates group assignments for the RGP cohort.

Families are divided into a train group and a holdout group. Grouping attempts to divide families with specific seqr
`TAGS_OF_INTEREST` into groups corresponding to the `prop_train` ratio. If a family has multiple `TAGS_OF_INTEREST` for
a given variant, or multiple variants for that family, grouping is applied via precedence order of `TAGS_OF_INTEREST`,
e.g., if tags of interest is [tag_a, tag_b], and a family has both tags, the tag considered for grouping purposes will
be tag_a.

usage: rgp_group_assigner.py [-h]
    --seqr_indiv SEQR_INDIV
    --seqr_tag SEQR_TAG
    [--prop_train PROP_TRAIN]
    [--samples SAMPLES]
    [--history HISTORY]
    --output OUTPUT

Options:
    --seqr_indiv FILE       path to an export of all individuals from a seqr project, can be defined multiple times,
                            e.g., --seqr_indiv indiv1.tsv --seqr_indiv indiv2.tsv. Multiple files are concatenated.
    --seqr_tag FILE         path to an export of all tagged variants from seqr, can be defined multiple times, e.g.,
                            --seqr_tag tag1.tsv --seqr_tag tag2.tsv. Multiple files are concatenated.
    --samples FILE          [optional] list of samples for which genetic data are available. If provided, only families 
                            for whom we have genetic data for all family members in `indiv` will be considered.
    --history FILE          [optional] output from a previous run of this script, used to ensure historical consistency.
    --output FILE           output filepath for group assignments, written as a tab-delimited file.
    -h, --help              show this screen
"""

import logging
from argparse import ArgumentParser
from typing import List

import pandas as pd

from lib.seqr.metadata import SeqrSubjects, SeqrTags

# This should never be changed.
PROP_TRAIN = 0.5


def get_family(id: str) -> str:
    """Return the family of a subject ID, defined as the first 2 tokens in the ID."""
    return "_".join(id.split("_")[0:2])


def parse_samples(path: str) -> pd.DataFrame:
    """Parse a list of subjects for which genetic data are available."""
    df = pd.read_csv(path, sep="\t", header=None, names=["subject_id"])
    df["family_id"] = df["subject_id"].apply(get_family)
    return df


def filter_indiv(indiv: SeqrSubjects, samples_df: pd.DataFrame | None) -> SeqrSubjects:
    # We only want to consider indivuals for whom we have data loaded into seqr.
    for subject in indiv.get_subjects():
        if not indiv.is_data_loaded(subject):
            indiv.remove_subject(subject)

    for family in indiv.get_families():
        # We only want to consider families with at least one affected individual
        found = False
        for subject in indiv.get_subjects_for_family(family):
            if indiv.is_affected(subject):
                found = True
                break
        if not found:
            indiv.remove_family(family)

    # If samples are provided, we only want to consider families for whom all family members from seqr are also listed
    # in samples. This is relevant because we don't want solved cases from seqr to have access to additional information
    # than what will be available to AIP.
    if samples_df is not None:
        for family in indiv.get_families():
            for subject in indiv.get_subjects_for_family(family):
                if subject not in samples_df["subject_id"].values:
                    indiv.remove_family(family)
                    break

    return indiv


def main(
    seqr_indiv: List[str], seqr_tag: List[str], samples: str, prop_train: float, history: str, output: str
) -> None:
    tags = SeqrTags.parse(seqr_tag)
    indiv = SeqrSubjects.parse(seqr_indiv)

    # Filter the subject records from seqr.
    indiv = filter_indiv(indiv, parse_samples(samples) if samples else None)

    # Assign groups based on tags.
    assignments_df = pd.DataFrame(
        data={
            "family_id": indiv.get_families(),
            "group": None,
            "tag": [tags.get_highest_precedence_tag(family) for family in indiv.get_families()],
        }
    ).set_index("family_id")
    assignments_df.tag.fillna("untagged", inplace=True)

    # Add in history if provided
    if history:
        history_df = pd.read_csv(history, sep="\t").set_index("family_id")
        assignments_df.update(history_df, overwrite=True)
        logging.info(f"Loaded {len(history_df)} assignments from {history}")

    # Randomly assign groups based on tags, ignoring families that have already been assigned.
    assigned = 0
    for tag in assignments_df.tag.unique():
        # Hard assumption here of exactly two groups, train and holdout.
        # Find and shuffle the families that we need to assign groups to.
        families_to_assign = assignments_df[assignments_df.group.isna() & (assignments_df.tag == tag)]
        families_to_assign_shuffled = families_to_assign.sample(frac=1)
        # Figure out how many new train assignments are needed to keep target proportion.
        n_tagged_train = ((assignments_df.group == "train") & (assignments_df.tag == tag)).sum()
        n_train_new = int((assignments_df.tag == tag).sum() * prop_train) - n_tagged_train

        assignments_df.loc[families_to_assign_shuffled[:n_train_new].index, "group"] = "train"
        assignments_df.loc[families_to_assign_shuffled[n_train_new:].index, "group"] = "holdout"

        logging.info(f"Assigning groups for tag {tag}: {len(families_to_assign)} newly tagged.")
        assigned += len(families_to_assign)

    logging.info(f"Assigned {assigned} families to groups.")

    # Write out the new assignments.
    logging.info(f"Writing group assignments to {output}")
    assignments_df.to_csv(output, sep="\t")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--seqr_indiv", action="append", required=True)
    parser.add_argument("--seqr_tag", action="append", required=True)
    parser.add_argument("--samples", required=False)
    parser.add_argument("--history", required=False)
    parser.add_argument("--output", required=True)

    logging.basicConfig(level=logging.INFO)

    args = parser.parse_args()
    main(
        seqr_indiv=args.seqr_indiv,
        seqr_tag=args.seqr_tag,
        samples=args.samples,
        prop_train=PROP_TRAIN,
        history=args.history,
        output=args.output,
    )
