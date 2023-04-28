"""Simple workbook to generate a group assignment history file for the CAGI subset of the RGP cohort.

All the families in this subset can be assumed to be in train, but we need to figure out what the appropriate
tag for each of them will be so we can assign future families in such a way that maintains tag balance.
"""

# %% Imports.
import pandas as pd

from src.seqr.metadata import SeqrTags

# %% Constants.
FAM_PATH = "~/data/rgp/cagi_pedigree.fam"
HISTORY_PATH = "~/data/rgp/cagi_history.tsv"

TAG_PATHS = [
    "~/data/rgp/metadata/saved_all_variants_rare_genomes_project_genomes_hmb.tsv",
    "~/data/rgp/metadata/saved_all_variants_rare_genomes_project_genomes_gru.tsv",
]

# %% Read in data.

seqr_tags = SeqrTags.parse(TAG_PATHS)

fam_df = pd.read_csv(FAM_PATH, sep="\t", header=None).rename(
    columns={0: "family_id", 1: "sample_id", 2: "maternal_id", 3: "paternal_id", 4: "sex", 5: "affected"}
)
fam_df = fam_df.groupby("family_id").apply(lambda x: x.iloc[0])

fam_df["tag"] = fam_df.family_id.apply(lambda x: seqr_tags.get_highest_precedence_tag(x))  # type: ignore
fam_df["tag"] = fam_df["tag"].fillna("untagged")
fam_df["group"] = "train"

fam_df.filter(["family_id", "group", "tag"]).to_csv(HISTORY_PATH, sep="\t", index=False)

# %%
