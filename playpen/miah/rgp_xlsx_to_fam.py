"""Ingest the RGP meta-data xlsx and generate a corresponding plink-formatted FAM file.

File of interest can be localized to the tempdir with the following commands on an Azure VM:
sudo mkdir /mnt/data
sudo chmod a+rw /mnt/data

az storage blob download -n /joint-called-vcf_20221114/RGP_Cases_for_MSFT_AIP_v0_trial.xlsx -c rgp --account-name \
controlleddata -f /mnt/data/RGP_Cases_for_MSFT_AIP_v0_trial.xlsx --auth-mode login

With default parameters, the resultant file can be written back to the appropriate location with:

az storage blob upload -f /mnt/data/RGP_Cases_for_MSFT_AIP_v0_trial.xlsx.fam --blob-url \
https://controlleddata.blob.core.windows.net/rgp/joint-called-vcf_20221114/RGP_Cases_for_MSFT_AIP_v0_trial.xlsx.fam \
--auth-mode login
"""

import os

import click
import pandas as pd


class Pedigree:
    _df: pd.DataFrame

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> "Pedigree":
        """Generates a Pedigree object from a source `pandas.DataFrame`.

        Input dataframe must contain exactly six columns, corresponding to the PLINK fam file format:
        https://www.cog-genomics.org/plink/1.9/formats#fam
        """
        instance = Pedigree()
        instance._df = df
        return instance

    def write_to_file(self, target: str) -> None:
        """Write the pedigree to a file."""
        self._df.to_csv(target, sep="\t", header=False, index=False)


class XlsxPedigreeParser:
    def __init__(self, src: str) -> None:
        self.src = src

    def _clean_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        mapping = {x: x.strip() for x in df.columns.values if x != x.strip()}
        return df.rename(columns=mapping)

    def _assign_parent(self, df: pd.DataFrame, relationship: str) -> pd.Series:
        parents = (
            df[["family_id", "subject_id"]].loc[df["RELATIONSHIP TO PROBAND"] == relationship].set_index("family_id")
        )
        return df.apply(
            lambda row: parents.loc[row.family_id].subject_id
            if row.family_id in parents.index and row.is_child
            else "0",  # type: ignore
            axis=1,
        )

    def parse(self, sheet:str = None) -> Pedigree:
        """Parse the xlsx file and return a Pedigree object.

        Will raise an error if the following columns are not present:
        - family_id
        - subject_id
        - RELATIONSHIP TO PROBAND (values be one of: Mother, Father, Self, Sibling)
        - SEX (values must be one of: Female, Male)
        - AFFECTED STATUS (values must be one of: Affected, Unaffected)
        """
        dfs = pd.read_excel(self.src, sheet_name=None)

        for sheet_name, df in dfs.items():
            dfs[sheet_name] = self._clean_columns(df)

        df = pd.concat(dfs.values(), ignore_index=True)
        
        # Generate the father/mother columns.
        df["is_child"] = df["subject_id"].str.endswith("3") | df["subject_id"].str.endswith("4")
        df["paternal_id"] = self._assign_parent(df, "Father")
        df["maternal_id"] = self._assign_parent(df, "Mother")

        # Recode and rename the sex column.
        df["SEX"] = df["SEX"].map({"Male": 1, "Female": 2, "Unknown": 0})
        df.rename(columns={"SEX": "sex"}, inplace=True)

        # Recode the affected status column.
        df["AFFECTED STATUS"] = df["AFFECTED STATUS"].map({"Affected": 2, "Unaffected": 1})
        df.rename(columns={"AFFECTED STATUS": "phenotype"}, inplace=True)

        # Select and order relevant columns.
        kept_column_order = ["family_id", "subject_id", "paternal_id", "maternal_id", "sex", "phenotype"]

        p = Pedigree.from_dataframe(df[kept_column_order].copy())
        return p


@click.command()
@click.option("--xlsx_path", required=True, type=click.Path(exists=True))
@click.option("--fam_path", default=None)
@click.option("--overwrite", is_flag=True, default=False)
def main(xlsx_path: str, fam_path: str, overwrite: bool) -> None:
    if not fam_path:
        fam_path = xlsx_path + ".fam"
    if os.path.exists(fam_path) and not overwrite:
        raise ValueError("The destination for --fam_path exists, set the --overwrite flag and re-run to overwrite.")

    ped = XlsxPedigreeParser(xlsx_path).parse()
    ped.write_to_file(fam_path)

    print("Successfully wrote FAM file to: " + fam_path)


if __name__ == "__main__":
    main()
