from pathlib import Path

import Bio
import typer
from Bio.PDB import PDBIO, MMCIFParser, Select

app = typer.Typer()


class NoUNKSelect(Select):
    def accept_residue(self, residue: Bio.PDB.Residue.Residue) -> bool:
        to_return: bool = residue.get_resname() != "UNK"
        return to_return


@app.command()
def main(
    input_cifs: list[str] = typer.Argument(..., help="List of input CIF files"),
    output_dir: str = typer.Argument(..., help="Output directory for PDB files"),
) -> None:
    for cif_file in input_cifs:
        output_pdb = Path(output_dir) / Path(Path(cif_file).name).with_suffix(".pdb")
        convert_cif_to_pdb(Path(cif_file), output_pdb)


def sanitize_pdb(pdb_path: Path) -> None:
    """Replace non-ASCII bytes in a PDB file with spaces in-place."""
    raw = pdb_path.read_bytes()
    sanitized = bytes(b if b < 128 else ord(" ") for b in raw)
    if sanitized != raw:
        pdb_path.write_bytes(sanitized)


def convert_cif_to_pdb(input_cif: Path, output_pdb: Path) -> None:
    parser = MMCIFParser()
    struc = parser.get_structure("", str(input_cif))

    io = PDBIO()
    io.set_structure(struc)
    io.save(str(output_pdb), select=NoUNKSelect())
    sanitize_pdb(output_pdb)


if __name__ == "__main__":
    app()
