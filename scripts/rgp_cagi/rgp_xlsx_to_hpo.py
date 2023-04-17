"""Ingest the RGP meta-data xlsx and generate a corresponding file of HPO terms per sample.

File of interest can be localized to the tempdir with the following commands on an Azure VM:
sudo mkdir /mnt/data -m a+rw

az storage blob download -n /joint-called-vcf_20221114/RGP_Cases_for_MSFT_AIP_v0_trial.xlsx -c rgp --account-name \
controlleddata -f /mnt/data/RGP_Cases_for_MSFT_AIP_v0_trial.xlsx --auth-mode login

With default parameters, the resultant file can be written back to the appropriate location with:

az storage blob upload -f /mnt/data/RGP_Cases_for_MSFT_AIP_v0_trial.xlsx.fam --blob-url \
https://controlleddata.blob.core.windows.net/rgp/joint-called-vcf_20221114/RGP_Cases_for_MSFT_AIP_v0_trial.xlsx.fam \
--auth-mode login
"""

import os
import re
from typing import Optional

import click
import pandas as pd


class HpoPhenotype:
    _df: pd.DataFrame

    @classmethod
    def _parse_phenotype_column(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Parse the hpo_terms column into a series of rows with a single HPO term per row."""

        def column_regex(value: str | float):
            if not isinstance(value, float):
                return re.findall("HP:[0-9]+", value)
            else:
                return []

        df["hpo_terms"] = df["hpo_terms"].apply(column_regex)
        return df

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> "HpoPhenotype":
        """Generates a HpoPhenotype object from a source `pandas.DataFrame`.

        Input dataframe must contain exactly three columns, family_id, subject_id, and HPO PRESENT
        """
        instance = HpoPhenotype()
        instance._df = HpoPhenotype._parse_phenotype_column(df.copy())
        return instance

    def write_to_file(self, target: str) -> None:
        """Write the pedigree to a file."""
        self._df.set_index("subject_id").to_json(target, orient="index", indent=4)


class XlsxHpoPhenotypeParser:
    def __init__(self, src: str) -> None:
        self.src = src

    def _clean_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        mapping = {x: x.strip() for x in df.columns.values if x != x.strip()}
        return df.rename(columns=mapping)

    def parse(self, sheet: Optional[str] = None) -> HpoPhenotype:
        """Parse the xlsx file and return an HpoPhenotype object.

        Optionally provide a sheet name to parse a single sheet.

        Will raise an error if the following columns are not present:
        - family_id
        - subject_id
        - HPO PRESENT (values should be `|`-separated HPO terms or NaN)
        """
        if not sheet:
            dfs = pd.read_excel(self.src, sheet_name=None)

            for sheet_name, df in dfs.items():
                dfs[sheet_name] = self._clean_columns(df)

            df = pd.concat(dfs.values(), ignore_index=True)
        else:
            df = pd.read_excel(self.src, sheet_name=sheet)
            df = self._clean_columns(df)

        # Rename HPO PRESENT column.
        df.rename(columns={"HPO PRESENT": "hpo_terms"}, inplace=True)

        # Select and order relevant columns.
        kept_column_order = ["family_id", "subject_id", "hpo_terms"]

        p = HpoPhenotype.from_dataframe(df[kept_column_order])

        return p


@click.command()
@click.option("--xlsx_path", required=True, type=click.Path(exists=True))
@click.option("--hpo_path", default=None)
@click.option("--sheet", default=None)
@click.option("--overwrite", is_flag=True, default=False)
def main(xlsx_path: str, hpo_path: str, sheet: str, overwrite: bool) -> None:
    if not hpo_path:
        hpo_path = xlsx_path + ".hpo.json"
    if os.path.exists(hpo_path) and not overwrite:
        raise ValueError("The destination for --hpo_path exists, set the --overwrite flag and re-run to overwrite.")

    hpo = XlsxHpoPhenotypeParser(xlsx_path).parse(sheet=sheet)
    hpo.write_to_file(hpo_path)

    print("Successfully wrote HPO file to: " + hpo_path)


if __name__ == "__main__":
    main()
