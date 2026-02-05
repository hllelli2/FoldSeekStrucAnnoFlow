from pathlib import Path

import typer
from Bio.PDB import PDBIO, MMCIFParser

app = typer.Typer()


@app.command()
def main(
    input_cifs: list[str] = typer.Argument(..., help="List of input CIF files"),
    output_dir: str = typer.Argument(..., help="Output directory for PDB files"),
) -> None:
    for cif_file in input_cifs:
        output_pdb = Path(output_dir) / Path(Path(cif_file).name).with_suffix(".pdb")
        convert_cif_to_pdb(Path(cif_file), output_pdb)


def convert_cif_to_pdb(input_cif: Path, output_pdb: Path) -> None:
    parser = MMCIFParser()
    struc = parser.get_structure("", str(input_cif))

    io = PDBIO()
    io.set_structure(struc)
    io.save(str(output_pdb))


if __name__ == "__main__":
    app()
