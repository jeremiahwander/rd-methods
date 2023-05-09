"""Workbook to explore splitting an input VCF file into folds/groups."""

# Note, this workbook will leverage Hail Query, and for large VCFs it's recommended to use Query-on-Batch or Spark to
# parallelize execution. Configuration of Hail will occur outside of this workbook.
#
# If you're running using the local backend for Hail Query (this is default), you'll need a few pre-requisites
#
# sudo apt-get install -y \
#     openjdk-8-jre-headless \
#     g++ \
#     python3.8 python3-pip \
#     libopenblas-base liblapack3
#
# To run using QoB, you'll need to set the following settings (either via env var, or hailctl CLI):
# - domain
# - batch/billing_project
# - batck/remote_tmpdir
# - query/backend
#
# And potentially the following if the SHA for the build of hail that you're using isn't the same as one of the JAR
# files supported by your Hail cluster:
# - query/jar_url
#
# Also note that running Query-on-Batch may require a more sophisticated environment setup than this repo supports.
# Specifically, QoB may require that your environment has a specific version of the Hail package installed to be
# compatible with the version of Hail running on the cluster.
#
# To address this, you'll want to remove the installed version of Hail via `poetry remove hail` and then manually
# install the version of hail from source that you want. Follow the approach used in this dockerfile:
# https://github.com/populationgenomics/analysis-runner/blob/07c384ed90c447b480f3b68b78f224e7eb301384/driver/Dockerfile.hail#L29
#
# Files needed:
#  - VCF file
#  - file specifying folds/groups, in this case we'll use an output from scripts/rgp/rgp_group_assigner.py, so groups
#    will be indexed by family ID (e.g., RGP_123).
#

# %% Imports.
from collections import defaultdict

import hail as hl
import pandas as pd

# %% Constants.

# VCF Path. If this path points to a .bgz file, an appropriate index file must also exist.
# Currently only GRCh38 is supported. This isn't really relevant for the purposes of this script, but Hail requires
# that we specify reference genome, so we will.
VCF_PATH = "/mnt/data/rgp/1kg.vcf.bgz"

# Group assignment file path.
GROUPS_PATH = "~/data/rgp/group_assignments.tsv"


# %% Configure Hail.
hl.init()

# %% Load the VCF into a Hail MatrixTable.
mt = hl.import_vcf(VCF_PATH, reference_genome="GRCh38")

vcf_samples = mt.s.collect()

# %% Load the group assignments.
groups_df = pd.read_csv(GROUPS_PATH, sep="\t")
samples_to_keep = defaultdict(list)

for group, group_df in groups_df.groupby("group"):
    samples_to_keep[group] = group_df["indiv_ids"].str.split("|").explode().tolist()

# %% Error checking.
# Are there samples in samples_to_keep that aren't in the VCF?
all_kept_samples = [ssub for s in samples_to_keep.values() for ssub in s]
missing_from_vcf = set(all_kept_samples) - set(vcf_samples)
if missing_from_vcf:
    raise ValueError(f"Samples {missing_from_vcf} are in the group assignment but missing from the VCF.")
else:
    print("No samples are in the group assignment but missing from the VCF.")

# Are there samples in the VCF that aren't in samples_to_keep?
missing_from_group_assignments = set(vcf_samples) - set(all_kept_samples)
if missing_from_group_assignments:
    raise ValueError(f"Samples {missing_from_group_assignments} are in the VCF but missing from the group assignments.")
else:
    print("No samples are in the VCF but missing from the group assignments.")

# %% Write out group assignments to file so that hail can use them.

for group, samples in samples_to_keep.items():
    mt_filtered = mt.filter_cols(hl.literal(samples).contains(mt.s))
    hl.export_vcf(mt_filtered, VCF_PATH.replace(".vcf.bgz", f".{group}.vcf.bgz"), tabix=True)
