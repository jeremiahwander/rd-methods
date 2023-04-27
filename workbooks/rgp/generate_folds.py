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

from collections import Counter, defaultdict
from typing import DefaultDict, List

import numpy as np
import pandas as pd

# %% CONSTANTS

# Path to metadata table.
CLIN_PATH = {
    "HMB": "~/data/rgp/metadata/rare_genomes project_genomes_hmb_individuals.tsv",
    "GRU": "~/data/rgp/metadata/rare_genomes project_genomes_gru_individuals.tsv",
}

# Path to sample list from vcf.
VCF_PATH = "~/data/rgp/samples.txt"

# Path to seqr export of tags.
SEQR_PATH = {
    "HMB": "~/data/rgp/metadata/saved_all_variants_rare_genomes_project_genomes_hmb.tsv",
    "GRU": "~/data/rgp/metadata/saved_all_variants_rare_genomes_project_genomes_gru.tsv",
}

OUT_DF_PATH = "~/data/rgp/rgp_folds_new.tsv"

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
    df.rename(columns={"Family ID": "family_id", "Individual ID": "subject_id"}, inplace=True)
    df["consent_group"] = consent_group
    clin_df = pd.concat([clin_df, df], ignore_index=True) if not clin_df.empty else df

vcf_df = pd.read_csv(VCF_PATH, sep="\t", header=None)
vcf_df.rename(columns={0: "subject_id"}, inplace=True)
vcf_df["family_id"] = vcf_df.subject_id.apply(lambda x: "_".join(x.split("_")[0:2]))

seqr_df = pd.DataFrame()
for consent_group, path in SEQR_PATH.items():
    df = pd.read_csv(path, sep="\t")
    df["consent_group"] = consent_group
    seqr_df = pd.concat([seqr_df, df], ignore_index=True) if not seqr_df.empty else df

# %% Manual hacks

# Drop RGP_1848 one of the two copies of all the members of RGP_1848.
# This family is present in both consent groups.
for sid in ["RGP_1848_1", "RGP_1848_2", "RGP_1848_3"]:
    clin_df.drop(clin_df.loc[(clin_df.subject_id == sid) & (clin_df.consent_group == "GRU")].index, inplace=True)


# %% Print some basic info about the data.
print(f"clin_df: {clin_df.shape}")
print(f"  contains {clin_df.family_id.nunique()} families")
print(
    f"  contains {clin_df.loc[clin_df['Individual Data Loaded'] == 'Yes'].family_id.nunique()} "
    "families with genetic data"
)
print(f"vcf_df: {vcf_df.shape}")
print(f"  contains {vcf_df.family_id.nunique()} families")

print(f"seqr_df: {seqr_df.shape}")
print(f"  contains {seqr_df.family.nunique()} families")

clin_all_families = clin_df.loc[clin_df["Individual Data Loaded"] == "Yes"].family_id.unique()
vcf_all_families = vcf_df.family_id.unique()
seqr_all_families = seqr_df.family.unique()
all_families = np.unique(np.concatenate([clin_all_families, vcf_all_families, seqr_all_families]))
print(f"all_families (with genetic data): {all_families.shape}")

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

# Show how many families have each tag.
counter = Counter(seqr_families.values())
tag_list = list(counter.keys())
tag_list.sort()
for tag in tag_list:
    print(f"{tag}: {counter[tag]}")

# %% The following sections apply to validating and pre-processing the clinical metadata table.
#
#
#

# %% Start by dropping subjects that do not have genetic data loaded, per the clinical metadata table.
print(f"before filtering: {clin_df.family_id.nunique()} families")
clin_df = clin_df.loc[clin_df["Individual Data Loaded"] == "Yes"]
print(f"after filtering: {clin_df.family_id.nunique()} families")

# %% Now drop all families for which no members of the family are affected.
print(f"before filtering: {clin_df.family_id.nunique()} families")
clin_df = clin_df.groupby("family_id").filter(lambda x: (x["Affected Status"] == "Affected").any())
print(f"after filtering: {clin_df.family_id.nunique()} families")


# %% We started by combining tables from potentially more than one source.
# Validate that no subjects are listed more than once.
if len(clin_df.subject_id) != len(set(clin_df.subject_id)):
    print("ERROR: Duplicate subjects found in clinical data table.")

    for sid in clin_df.subject_id.unique():
        if len(clin_df.loc[clin_df.subject_id == sid]) > 1:
            print(f"ERROR: Duplicate subject found: {sid}")
else:
    print("No duplicate subjects found in clinical data table.")

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

print(f"There are {len(fam_df)} families in total.")

# Check to make sure that every family was in the clinical metadata tables.
print(f"There were {len(fam_df) - fam_df.in_clin.sum()} absent from metadata")
print(f"There were {len(fam_df) - fam_df.in_vcf.sum()} absent from VCF")

# %% Trim out families that don't make the cut

# Remove families that are entirely absent from the clinical table.
fam_df = fam_df.loc[fam_df.in_clin]

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

# %% Build the pedigree files for the two groups.
# See https://www.cog-genomics.org/plink/1.9/formats#fam for detail on the correct format.
pedigree = clin_df.copy()
pedigree.Sex = pedigree.Sex.map({"Female": 2, "Male": 1, "Unknown": 0})
pedigree["Affected Status"] = pedigree["Affected Status"].map({"Affected": 2, "Unaffected": 1, "Unknown": 0})

kept_cols = ["family_id", "subject_id", "Paternal ID", "Maternal ID", "Sex", "Affected Status"]

# TODO
TRAIN_PED_PATH = "~/data/rgp/rgp_train.fam"
HOLDOUT_PED_PATH = "~/data/rgp/rgp_holdout.fam"

# TODO Pedigree QC.
# 1. Make sure that every family has at least one affected.
# 2. Make sure that anyone with the _1 or _2 family suffixes are referred to by other family members?
# 3. More?

# %% Export the pedigrees.
pedigree.loc[clin_df.family_id.isin(fam_df.loc[fam_df.is_train].family_id), kept_cols].to_csv(
    TRAIN_PED_PATH, sep="\t", index=False, header=False
)
pedigree.loc[clin_df.family_id.isin(fam_df.loc[~fam_df.is_train].family_id), kept_cols].to_csv(
    HOLDOUT_PED_PATH, sep="\t", index=False, header=False
)


# %% Build the HPO files for the two groups.


def hpo_string_to_list(hpo_string: str) -> List[str]:
    """Convert a semicolon-separated string of HPO terms to a list of HPO terms.

    Remove parenthetical content and whitespace.
    """
    if not isinstance(hpo_string, str):
        return []
    hpo_terms = hpo_string.split(";")
    hpo_terms = [term.split("(")[0].strip() for term in hpo_terms]
    return hpo_terms


# Build train and holdout_dicts from clin_df that follows this format.
# Need to iterate over families, not individuals, since at this point clin_df and vcf_df are not consistent.
train_dict = {}
holdout_dict = {}
for _, fam_row in fam_df.iterrows():
    family = fam_row.family_id
    is_train = fam_row.is_train

    for _, clin_row in clin_df.loc[clin_df.family_id == family].iterrows():
        subject = clin_row.subject_id
        hpo_terms = clin_row["HPO Terms (present)"]

        if is_train:
            train_dict[subject] = {"family_id": family, "hpo_terms": hpo_string_to_list(hpo_terms)}
        else:
            holdout_dict[subject] = {"family_id": family, "hpo_terms": hpo_string_to_list(hpo_terms)}

# TODO Write out the hpo files.

# %% Build the tag files for the two groups.

# Iterate through seqr_df and build a dictionary of tags for each family.

# We will use the TAGS_OF_INTEREST to determine which tags to keep, and will only keep the highest priority tag for a
# given variant/family. This was already pre-computed above.


def is_valid_variant(var_row: pd.Series) -> bool:
    """Returns true of chrom, pos, ref, and alt are all non-nan, false if otherwise."""
    return not any(pd.isna(var_row[x]) for x in ["chrom", "pos", "ref", "alt"])


train_tag_dict: DefaultDict[str, dict[str, List[str]]] = defaultdict(dict)
holdout_tag_dict: DefaultDict[str, dict[str, List[str]]] = defaultdict(dict)

for _, var_row in seqr_df.iterrows():
    if not is_valid_variant(var_row):
        continue
    if var_row.tag not in TAGS_OF_INTEREST:
        continue

    fam_row = fam_df.loc[fam_df.family_id == var_row.family]
    if len(fam_row) == 0:
        continue

    is_train = fam_row.is_train.values[0]

    var_str = "-".join([str(var_row.chrom), str(var_row.pos), var_row.ref, var_row.alt])
    likely_proband: str = next(
        (x for x in var_row.filter(like="sample_").values if isinstance(x, str) and int(x.split("_")[2]) >= 3),
        "",
    )

    if not likely_proband:
        print(f"Error: no proband candidate found for variant {var_str} in family {var_row.family}")
        continue

    print(f"Adding variant {var_str} to family {var_row.family}, likely proband {likely_proband}")

    if is_train:
        train_tag_dict[likely_proband][var_str] = var_row.tag
    else:
        holdout_tag_dict[likely_proband][var_str] = var_row.tag

# TODO Write out the tag files.

# %%
