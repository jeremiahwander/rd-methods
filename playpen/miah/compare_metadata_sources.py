"""Simple script to compare RGP metadata derived from Terra with metadata derived from seqr."""

# %% Imports.
import pandas as pd

# %% Constants.
SEQR_PATH = {
    "HMB": "~/data/rgp/metadata/rare_genomes project_genomes_hmb_individuals.tsv",
    "GRU": "~/data/rgp/metadata/rare_genomes project_genomes_gru_individuals.tsv",
}

TERRA_PATH = {
    "HMB": "~/data/rgp/clinical_subjects_table_2023.04.13.tsv",
    "GRU": "~/data/rgp/clinical_subjects_table_GRU_2023.04.24.tsv",
}

# %%
seqr_df = pd.DataFrame()
for consent_group, path in SEQR_PATH.items():
    df = pd.read_csv(path, sep="\t")
    df.rename(columns={"Family ID": "family_id", "Individual ID": "subject_id"}, inplace=True)
    df["consent_group"] = consent_group
    seqr_df = pd.concat([seqr_df, df], ignore_index=True) if not seqr_df.empty else df

terra_df = pd.DataFrame()
for consent_group, path in TERRA_PATH.items():
    df = pd.read_csv(path, sep="\t")
    df.rename(columns={"entity:subject_id": "subject_id"}, inplace=True)
    df["consent_group"] = consent_group
    terra_df = pd.concat([terra_df, df], ignore_index=True) if not terra_df.empty else df


# %% Preprocess dataframes
seqr_df = seqr_df.loc[seqr_df["Individual Data Loaded"] == "Yes"]

# %% Compare the subjects included in the two metadata

if len(set(terra_df["subject_id"]) - set(seqr_df["subject_id"])) != 0:
    raise ValueError(
        "We're working from the assumption that the terra_df contains a subset of the subjects in the seqr_df"
    )

seqr_df = seqr_df.loc[seqr_df["subject_id"].isin(terra_df["subject_id"])]

# %%
joined = pd.merge(seqr_df, terra_df, how="inner", on="subject_id")

# %% check some basic column equivalence


def match_hpo_value(s1, s2, split_token1, split_token2):
    """Check if the two Series of hpo values are equivalent, using split tokens."""
    nan_mask = s1.isna() & s2.isna()

    s1 = s1.str.replace(r"[\|; ]", "", regex=True)
    s2 = s2.str.replace(r"[\|; ]", "", regex=True)

    # remove text between parentheses
    s1 = s1.str.replace(r"\(.*?\)", "", regex=True)
    s2 = s2.str.replace(r"\(.*?\)", "", regex=True)

    # compare the two columns
    return (s1 == s2) | nan_mask


def find_hpo_differences(df, col1, col2):
    differences = df.loc[~match_hpo_value(df[col1], df[col2], "; ", "|"), ["subject_id", col1, col2]]
    print(f"Found {len(differences)} differences between {col1} and {col2}")
    return differences


col_pairs = [
    ("HPO Terms (present)", "hpo_present"),
    ("HPO Terms (absent)", "hpo_absent"),
]

for col1, col2 in col_pairs:
    differences = find_hpo_differences(joined, col1, col2)


# %%
def find_differences(df, col1, col2, print_differences=False):
    differences = df.loc[df[col1] != df[col2], ["subject_id", col1, col2]]
    print(f"Found {len(differences)} differences between {col1} and {col2}")
    if print_differences:
        print(differences)


col_pairs = [
    ("consent_group_x", "consent_group_y"),
    ("Affected Status", "affected_status"),
]

for col1, col2 in col_pairs:
    find_differences(joined, col1, col2, print_differences=True)
# %%
