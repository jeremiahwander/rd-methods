#!/usr/bin/env bash

python3 scripts/rgp/rgp_aip_input_generator.py \
    --seqr_indiv "$HOME/data/rgp/metadata/rare_genomes project_genomes_gru_individuals.tsv" \
    --seqr_indiv "$HOME/data/rgp/metadata/rare_genomes project_genomes_hmb_individuals.tsv" \
    --group_assignments "$HOME/data/rgp/group_assignments.tsv" \
    --output_dir "$HOME/data/rgp/aip_inputs"
