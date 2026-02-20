import zipfile
from pathlib import Path

import typer

app = typer.Typer()


APPROVED_EXTENSIONS = {".pdb", ".cif", ".mmcif"}


@app.command()
def main(
    zip_file: str = typer.Argument(..., help="Path to the zip file containing PDB / Cif files"),
    output_text_file: str = typer.Argument(..., help="Path to the output text file listing the extracted files"),
) -> None:
    with zipfile.ZipFile(zip_file, "r") as zip_ref, open(output_text_file, "w") as output_file:
        file_list = [
            Path(info.filename).stem
            for info in zip_ref.infolist()
            if not info.is_dir() and any(info.filename.endswith(ext) for ext in APPROVED_EXTENSIONS)
        ]
        for file_name in file_list:
            output_file.write(file_name + "\n")


if __name__ == "__main__":
    app()
