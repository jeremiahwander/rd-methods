#!/usr/bin/env bash

python3 scripts/rgp/rgp_group_assigner.py \
    --seqr_indiv "$HOME/data/rgp/metadata/rare_genomes project_genomes_gru_individuals.tsv" \
    --seqr_indiv "$HOME/data/rgp/metadata/rare_genomes project_genomes_hmb_individuals.tsv" \
    --seqr_tag   "$HOME/data/rgp/metadata/saved_all_variants_rare_genomes_project_genomes_gru.tsv" \
    --seqr_tag   "$HOME/data/rgp/metadata/saved_all_variants_rare_genomes_project_genomes_hmb.tsv" \
    --history "$HOME/data/rgp/cagi_history.tsv" \
    --samples "$HOME/data/rgp/samples.txt" \
    --output "$HOME/data/rgp/group_assignments.tsv"
