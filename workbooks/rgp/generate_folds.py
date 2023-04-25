"""generate_folds.py.

This script will examine the various sources of information available to determine the full set of subjects from the RGP
HMB and GRU consent groups.

Then, using tags downloaded from seqr, will divide the subjects based on presence of a particular tag at some specified
ratio.

The script will write out a table with a boolean indicator of whether a particular familiy is
in the training group or not.

TODO: mechanism for adding new people? Those with relevant labels? Those without?
TODO: mechanism for taking in previous fold specifications and updating them?

"""

# %% Imports.

import numpy as np
import pandas as pd

# %% CONSTANTS

# Path to metadata table.
CLIN_PATH = {
    "HMB": "~/data/rgp/clinical_subjects_table_2023.04.13.tsv",
    "GRU": "~/data/rgp/clinical_subjects_table_GRU_2023.04.24.tsv",
}

# Path to sample list from vcf.
VCF_PATH = "~/data/rgp/samples.txt"

# Path to seqr export of tags.
SEQR_PATH = "~/data/rgp/tags.tsv"

OUT_DF_PATH = "~/data/rgp/rgp_folds.tsv"

# List of tags from the seqr export that will be used for partitioning families.
# These are in precedence order, so in cases where multiple tags are present, the tag earlier in the list will take
# precedence for the purposes of family grouping
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

# List of subject identifier and sample identifier suffices that signify multiple WGS samples for a single subject.
MULTI_SAMPLE_SUFFICES = [
    "D1",
    "D2",
    "M1",
    "fbs",
    "muscle",
]

# Fraction of families from a given group that will be assigned to train.
PARTITION_TRAIN = 0.5


# %% Define a few helper functions.
def get_suffix(id: str) -> str:
    """Return the suffix of a subject ID, if present. Define suffix as the 4th token in the ID."""
    tokens = id.split("_")
    if (length := len(tokens)) > 5 or length < 3:
        raise ValueError(f"Unexpected subject ID: {id}")
    if len(tokens) < 4:
        return ""
    return tokens[3]


def has_subject_id_suffix(subject_id: str) -> bool:
    """Return True if the subject ID has a suffix, False otherwise."""
    return True if get_suffix(subject_id) else False


def get_id_root(id: str) -> str:
    """Return the root of a subject ID, defined as the first 3 tokens in the ID."""
    return "_".join(id.split("_")[0:3])


def get_family(id: str) -> str:
    """Return the family of a subject ID, defined as the first 2 tokens in the ID."""
    return "_".join(id.split("_")[0:2])


def apply_tag_precedence(tag_list: str) -> str:
    """Apply the precedence order for tags to a list of tags.

    Returns the highest precedence tag in the pipe-delimited
    input string.
    """
    tag_elts = tag_list.split("|")
    for tag in TAGS_OF_INTEREST:
        if tag in tag_elts:
            return tag
    return "untagged"


# %% Read in data, do a teeny bit of formatting.
clin_df = pd.DataFrame()

for consent_group, path in CLIN_PATH.items():
    df = pd.read_csv(path, sep="\t")
    df.rename(columns={"entity:subject_id": "subject_id"}, inplace=True)
    df["consent_group"] = consent_group
    clin_df = pd.concat([clin_df, df], ignore_index=True) if not clin_df.empty else df

vcf_df = pd.read_csv(VCF_PATH, sep="\t", header=None)
vcf_df.rename(columns={0: "subject_id"}, inplace=True)
vcf_df["family_id"] = vcf_df.subject_id.apply(lambda x: "_".join(x.split("_")[0:2]))

seqr_df = pd.read_csv(SEQR_PATH, sep="\t")

print(f"clin_df: {clin_df.shape}")
print(f"vcf_df: {vcf_df.shape}")
print(f"seqr_df: {seqr_df.shape}")

# %% The following sections apply to validating and pre-processing the seqr export table.
# ##
# ##

# %% Validate tags at the variant level.

# The format of the seqr tag export is a TSV with one row per variant, multiple tags for that variant, but just one
# family.

# Only one of the tags of interest should be present for any given family.
# If more than one tag is present, this is an error.
error_count = 0
for idx, row in seqr_df.iterrows():
    tag_elts = row.tags.split("|")
    count = sum([t in TAGS_OF_INTEREST for t in tag_elts])
    if count > 1:
        print(f"ERROR: More than one tag of interest found for family: {idx}: {row.family} / {row.tags}")
        error_count += 1

if error_count < 1:
    print("No errors found in tag export.")

# On my export from Jan 2023, the above code will generate the following errors:
# ERROR: More than one tag of interest found for family:
#   565: RGP_248 / Analyst high priority|Tier 2 - Phenotype expansion|Known gene for phenotype|Returned
# ERROR: More than one tag of interest found for family:
#   566: RGP_248 / Analyst high priority|Tier 2 - Phenotype expansion|Known gene for phenotype|Returned
# ERROR: More than one tag of interest found for family:
#   687: RGP_312 / Known gene for phenotype|Analyst high priority|Multi-Nucleotide Variant
#   |Known gene for phenotype|Analyst high priority|Multi-Nucleotide Variant|Returned

# Print out a list of tags that weren't listed in TAGS_OF_INTEREST, to see if there are any mistyped values or other
# errors.
all_tags = set()
for _, row in seqr_df.iterrows():
    tag_elts = row.tags.split("|")
    all_tags.update(tag_elts)

print(all_tags - set(TAGS_OF_INTEREST))
# On my export from Jan 2023, the above code doesn't show any other tags that are of concern.


# %% Filter the tag table by applying the precedence order for TAGS_OF_INTEREST and otherwise setting the tag to
# 'untagged'

# New column tag is the preferred tag for this variant.
seqr_df["tag"] = seqr_df.tags.apply(apply_tag_precedence)

# %% Validate tags at the family level.

sample_columns = [c for c in seqr_df.columns if c.startswith("sample_")]

family_fail_count = 0
for _, row in seqr_df.iterrows():
    if any(get_family(str(row[c])) != row.family for c in sample_columns if row[c] is not np.nan):
        print(f"ERROR: Samples from multiple families found for variant: {row.family} / {row.tags}")
        family_fail_count += 1
if family_fail_count < 1:
    print("No instances of more than one family per variant found in tag export.")

# Check whether any family now has more than one unique tag other than 'untagged',
for family, group_df in seqr_df.groupby("family"):
    if len(cool_tags := set(group_df.loc[group_df.tag != "untagged"].tag)) > 1:
        print(f"{family}: {list(cool_tags)}")

# On my report from Jan 2023, the above code shows that
# No instances of more than one family per variant found in tag export.
# RGP_1456: 'Known gene for phenotype', 'Tier 2 - Novel gene and phenotype'
# RGP_1713: 'Tier 1 - Novel gene for known phenotype', 'Known gene for phenotype'

# %% Create the family list with highest priority tag for each family.
# Here we will generate a list of families (from the list of variants in the seqr export) that tells us the highest
# priority tag for each family. We will only include families that have a variant with a tag of interest.
seqr_families = {}
for family, group_df in seqr_df.groupby("family"):
    for tag in TAGS_OF_INTEREST:
        if tag in set(group_df.tag):
            seqr_families[family] = tag
            break

# %% The following sections apply to validating and pre-processing the clinical metadata table.
# ##
# ##

# %% We started by combining tables from potentially more than one source.
# Validate that no subjects are listed more than once.
if len(clin_df.subject_id) != len(set(clin_df.subject_id)):
    print("ERROR: Duplicate subjects found in clinical data table.")
else:
    print("No duplicate subjects found in clinical data table.")

# %% Validate that there is exactly one proband listed per family.

errors = False
families_missing_proband = []
for family, group_df in clin_df.groupby("family_id"):
    if (count := sum(group_df.proband_relationship == "Self")) > 1:
        print(f"ERROR: More than one proband found for family: {family}")
        print(group_df.loc[group_df.proband_relationship == "Self"]["subject_id"])
        errors = True
    if count == 0:
        # Not throwing the following error: print(f"ERROR: No proband found for family: {family}")
        families_missing_proband.append(family)
        errors = True
if not errors:
    print("No errors found in proband validation.")
else:
    print(f"Errors found in proband validation for {len(families_missing_proband)} families.")
    print(
        clin_df.loc[clin_df.family_id.isin(families_missing_proband)]
        .groupby("family_id")
        .apply(lambda x: x.iloc[0].consent_group)
        .value_counts()
    )

print(families_missing_proband)
# As of April 2024, a total of 54 families are missing a proband annotation.
# Notable that the GRU group, which is much smaller than the HMB group, has a much higher rate of missing probands.

# Observing that there is no proband for family is not a blocking issue, it just means that we won't have HPO for that
# particular proband (if we have genetic data), and that family structure will need to be inferred from other fields in
# the metadata spreadsheet.

# Potentially flag these missing data from the seqr team.

# %% Other proband/HPO validation checks
is_putative_proband = clin_df.subject_id.str.endswith("_3") & ~clin_df.subject_id.apply(has_subject_id_suffix)
is_putative_mother = clin_df.subject_id.str.endswith("_1") & ~clin_df.subject_id.apply(has_subject_id_suffix)
is_putative_father = clin_df.subject_id.str.endswith("_2") & ~clin_df.subject_id.apply(has_subject_id_suffix)

missing_relationship = clin_df.proband_relationship.isna()

# Determine which of the families that are missing a proband LACK a putative proband, where putative proband is
# defined as a subject_id that ends in _3 and does not have a suffix (e.g., _fbs).
clin_families_without_proband = set(families_missing_proband) - set(
    clin_df.loc[clin_df.family_id.isin(families_missing_proband) & is_putative_proband].family_id
)

print(
    f"The following {len(clin_families_without_proband)} families "
    f"have no true or putative proband: {clin_families_without_proband}"
)

# Let's check to see if any of these families are in the VCF.
vcf_families = set(vcf_df.subject_id.apply(lambda x: "_".join(x.split("_")[0:2])))
for family in clin_families_without_proband:
    if family in vcf_families:
        print(f"ERROR: Family {family} is in the VCF.")

# %%
# Let's see if any of the families missing an annotated proband happen to have HPO terms for other family members.
print(
    clin_df.loc[clin_df.family_id.isin(families_missing_proband) & ~clin_df.hpo_present.isna()][
        ["subject_id", "proband_relationship", "consent_group"]
    ]
)

# Wow there are a bunch of them! And many seem to be putative probands given the subject_id (ending in _3).

# %% Given the above, let's make a principled adjustment to proband_relationship in these cases where we have a
# best guess as to which subject is the proband.

do_infer_proband_self = (
    clin_df.family_id.isin(families_missing_proband) & ~clin_df.hpo_present.isna() & is_putative_proband
)

do_infer_proband_mother = is_putative_mother & missing_relationship
do_infer_proband_father = is_putative_father & missing_relationship

# Print some stats on what we're going to change.
print(f"Going to set {do_infer_proband_self.sum()} putative probands missing relationship to 'Self'")
print(f"Going to set {do_infer_proband_mother.sum()} putative proband-mothers missing relationship to 'Mother'")
print(f"Going to set {do_infer_proband_father.sum()} putative proband-fathers missing relationship to 'Father'")


# Actually make the changes.
clin_df.loc[do_infer_proband_self, "proband_relationship"] = "Self"
clin_df.loc[is_putative_mother & missing_relationship, "proband_relationship"] = "Mother"
clin_df.loc[is_putative_father & missing_relationship, "proband_relationship"] = "Father"

# %% Logic for definining the list of families
# Start with a union of the families included in the seqr output, the metadata table, and the VCF.
# Annotate each family with the highest priority seqr tag that applies to it.

vcf_fam_df = pd.DataFrame(data=vcf_df.family_id.unique(), columns=["family_id"])
vcf_fam_df["in_vcf"] = True

clin_fam_df = pd.DataFrame(data=clin_df.family_id.unique(), columns=["family_id"])
clin_fam_df["in_clin"] = True

seqr_fam_df = pd.DataFrame(data=seqr_df.family.unique(), columns=["family_id"])

fam_df = pd.merge(
    pd.merge(vcf_fam_df, clin_fam_df, how="outer", on="family_id"), seqr_fam_df, how="outer", on="family_id"
).fillna(False)

fam_df["seqr_tag"] = fam_df.family_id.apply(lambda x: seqr_families.get(x, "untagged"))

# Check to make sure that every family was in the clinical metadata tables.
print(f"There were {len(fam_df) - fam_df.in_clin.sum()} absent from metadata")
print(f"There were {len(fam_df) - fam_df.in_vcf.sum()} absent from VCF")

# %% Trim out families that don't make the cut

# remove families that are in clin_families_without_proband
fam_df = fam_df.loc[~fam_df.family_id.isin(clin_families_without_proband)]

# Remove families that are entirely absent from the VCF.
fam_df = fam_df.loc[fam_df.in_vcf]

# %% Highlight families where the list of subjects in the vcf doesn't match the list of subjects in the clin table.
fam_sub_mismatch = []
count_good = 0

for _, row in fam_df.iterrows():
    family = row.family_id
    clin_subjects = set(clin_df.loc[clin_df.family_id == family].subject_id)
    vcf_subjects = set(vcf_df.loc[vcf_df.family_id == family].subject_id)
    if not clin_subjects == vcf_subjects:
        print(f"Family {family} has a mismatch between the subjects in the clin table and the vcf table.")
        print(f"Subjects in clin table: {clin_subjects}")
        print(f"Subjects in vcf table: {vcf_subjects}")
        fam_sub_mismatch.append(family)
    else:
        count_good += 1

print(f"Found {len(fam_sub_mismatch)} families with mismatched subjects.")
print(f"Found {count_good} families with matching subjects.")

# This currently finds around 30 families with mismatched subjects between the VCF and the clinical metadata table.
# The only family that currently seems recoverable out of this list is RGP_800.

# %% Remove families with mismatched subjects.
fam_df = fam_df.loc[~fam_df.family_id.isin(fam_sub_mismatch)]

# %% Build train/holdout split.

# At this point, we are confident we have a proband, and can thus make a pedigree and have WGS data to back it up.
# We want to split the families into a training set and a holdout set, based on the seqr tags.

# First, let's provide a couple details about the families we're working with.
print(f"Total number of families remaining: {len(fam_df)}")
for tag in fam_df.seqr_tag.unique():
    print(f"{tag}: {len(fam_df.loc[fam_df.seqr_tag == tag])}")


# %% Assign a group label to each family.


def assign_probability(group_df: pd.DataFrame) -> np.ndarray:
    """Assign a probability of being in the training set to each family."""
    raw_probabilities = np.random.uniform(size=len(group_df))
    p_eps = 1 / len(group_df)

    # Fine tune the raw probabilities so we get as close to PARTITION_TRAIN as possible.
    if (raw_probabilities < PARTITION_TRAIN).mean() < PARTITION_TRAIN:
        # There are too few low values in raw_probabilities
        while (raw_probabilities < PARTITION_TRAIN).mean() < PARTITION_TRAIN:
            raw_probabilities[np.random.choice(len(raw_probabilities))] -= p_eps
    elif (raw_probabilities < PARTITION_TRAIN).mean() > PARTITION_TRAIN:
        # There are too many low values in raw_probabilities (too many families assigned to train)
        while (raw_probabilities < PARTITION_TRAIN).mean() > PARTITION_TRAIN:
            raw_probabilities[np.random.choice(len(raw_probabilities))] += p_eps

    return raw_probabilities


probs = fam_df.groupby("seqr_tag").family_id.transform(assign_probability)

fam_df["is_train"] = probs < PARTITION_TRAIN

# %% Double check our work to make sure we've got the right breakdown.

for group in fam_df.groupby("seqr_tag"):
    print(f"{group[0]} (N={len(group[1].is_train)}): proportion train = {group[1].is_train.mean()}")

# %% Write out the groups
print(f"Writing out the groups to {OUT_DF_PATH}")
fam_df.drop(["in_vcf", "in_clin"], axis=1).set_index("family_id").to_csv(OUT_DF_PATH)

# %%
