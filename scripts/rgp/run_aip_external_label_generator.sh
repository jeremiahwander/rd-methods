#!/usr/bin/env bash

python3 scripts/rgp/rgp_aip_external_label_generator.py \
    --seqr_tag "$HOME/data/rgp/metadata/saved_all_variants_rare_genomes_project_genomes_gru.tsv" \
    --seqr_tag "$HOME/data/rgp/metadata/saved_all_variants_rare_genomes_project_genomes_hmb.tsv" \
    --group_assignments "$HOME/data/rgp/group_assignments.tsv" \
    --output_dir "$HOME/data/rgp/aip_inputs"
