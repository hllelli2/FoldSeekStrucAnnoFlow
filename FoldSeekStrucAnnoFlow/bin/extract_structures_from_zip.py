import zipfile
from pathlib import Path

import typer

app = typer.Typer()


@app.command()
def main(
    pdb_zip: str = typer.Argument(..., help="Path to the zip file containing PDB / Cif files"),
    id_file: str = typer.Argument(..., help="Path to the text file containing the list of IDs to extract"),
) -> None:
    with open(id_file) as f:
        ids = [line.strip() for line in f if line.strip()]

    with zipfile.ZipFile(pdb_zip, "r") as z:
        zip_names = z.namelist()

        files = [Path(name) for name in zip_names if not Path(name).is_dir() and Path(name).stem in ids]

        for file in files:
            output_path = Path(file.name)
            with z.open(str(file)) as source, open(output_path, "wb") as target:
                target.write(source.read())


if __name__ == "__main__":
    app()
