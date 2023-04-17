"""explore_metadata.py.

This script performs comparisons of the list of samples provided in a SRC vcf
with the metadata available on the RGP cohort (specifically HPO terms).
"""

# %% Imports
import pandas as pd

# %% Data paths
# Exported clinical metadata table from Terra RGP Terra workspace.
clin_path = "~/data/rgp/clinical_subjects_table_2023.04.13.tsv"

# Pointer to a text file extracted from the full RGP vcf, using the following command:
# bcftools query -l <src_vcf> > <dest_txt>
vcf_path = "~/data/rgp/samples.txt"

# %% Read in data
clin_df = pd.read_csv(clin_path, sep="\t")
vcf_df = pd.read_csv(vcf_path, sep="\t", header=None)

print(f"clin_df: {clin_df.shape}")
print(f"vcf_df: {vcf_df.shape}")


# %% Define helper methods
def truncate_sid(sid: str) -> str:
    """Return the first three parts of a sample ID, separated by underscores."""
    return "_".join(sid.split("_")[:3])


def get_suffix(sid: str) -> str:
    """Return the last (4th) part of a sample ID, assuming it exists."""
    return "_".join(sid.split("_")[3:])


def has_suffix(sid: str) -> bool:
    """Returns true if the sample ID has a 4th part."""
    return len(sid.split("_")) > 3


def has_confusing_suffix(sid: str) -> bool:
    """Specifically returns suffices that I do not yet understand."""
    terms = sid.split("_")
    if len(terms) <= 3:
        return False
    return terms[3] in ["1", "2"]


# %% Process the VCF df a bit
vcf_df.rename(columns={0: "id"}, inplace=True)
vcf_df["in_vcf"] = True
vcf_df["id_short"] = vcf_df.id.apply(truncate_sid)

# %% Process the clinical df a bit
clin_df["id"] = clin_df["entity:subject_id"]
clin_df["is_parent"] = clin_df.id.str.endswith("_1") | clin_df.id.str.endswith("_2")
clin_df["in_clin"] = True
clin_df["id_short"] = clin_df.id.apply(truncate_sid)

# %% Get the list of ids that are in the VCF and not in the Clinical Data
missing_from_clin = list(set(vcf_df.id) - set(clin_df.id))
missing_from_clin.sort()
print(len(missing_from_clin))
print(", ".join(missing_from_clin))

# %% Get the list of ids that are in the Clinical Data and not in the VCF
missing_from_vcf = list(set(clin_df.id) - set(vcf_df.id))
missing_from_vcf.sort()
print(len(missing_from_vcf))
print(", ".join(missing_from_vcf))

# %% Get the list of all SIDs that have confusing suffices
suffix_sids = [s for s in clin_df.id if has_confusing_suffix(s)]
suffix_sids.sort()
print(len(suffix_sids))
print(", ".join(suffix_sids))

# %% Ask which affecteds (and probands) are missing HPO
affecteds_missing_hpo = list(
    clin_df.id.loc[(clin_df.affected_status == "Affected") & clin_df.hpo_present.isna() & clin_df.hpo_absent.isna()]
)
affecteds_missing_hpo.sort()
print(len(affecteds_missing_hpo))
print(", ".join(affecteds_missing_hpo))
probands_missing_hpo = [p for p in affecteds_missing_hpo if p.endswith("_3")]
print(len(probands_missing_hpo))
print(", ".join(probands_missing_hpo))

# %%
