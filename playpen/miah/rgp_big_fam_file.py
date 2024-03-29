#!/usr/bin/env python3

"""This python script generates the input files required by the AIP for the RGP cohort.

The following output files are generated by this script:
    - rgp_pedigree.fam
    - rgp_hpo.json

usage: rgp_big_fam_file.py.py [-h]
    --seqr_indiv SEQR_INDIV
    --output_dir OUTPUT_DIR

Options:
    --seqr_indiv FILE           path to an export of all individuals from a seqr project, can be defined multiple times,
                                e.g., --seqr_indiv indiv1.tsv --seqr_indiv indiv2.tsv. Multiple files are concatenated.
    --output_dir DIR            path to an output directory to write files to. Defaults to current working directory. If
                                the directory does not exist, it will be created.
    -h, --help                  show this screen
"""

import logging
import os
from argparse import ArgumentParser
from typing import List

from lib.seqr.io import HpoWriter, PedigreeWriter
from lib.seqr.metadata import SeqrSubjects


def main(seqr_indiv: List[str], output_dir: str) -> None:
    if not os.path.exists(output_dir):
        logging.warning(f"Output directory {output_dir} does not exist, creating it.")
        os.makedirs(output_dir)

    indiv = SeqrSubjects.parse(seqr_indiv)

    pedigree_file = os.path.join(output_dir, "pedigree.fam")
    logging.info(f"Writing pedigree file to {pedigree_file}")
    PedigreeWriter(indiv, families_to_write=indiv.get_families()).write(pedigree_file)
    hpo_file = os.path.join(output_dir, "hpo.json")
    logging.info(f"Writing HPO file to {hpo_file}")
    HpoWriter(indiv, families_to_write=indiv.get_families()).write(hpo_file)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--seqr_indiv", action="append", required=True)
    parser.add_argument("--output_dir", required=False, default=os.getcwd())

    logging.basicConfig(level=logging.INFO)

    args = parser.parse_args()
    main(
        seqr_indiv=args.seqr_indiv,
        output_dir=args.output_dir,
    )
