# Adapted from https://github.com/LBM-EPFL/PeSTo/blob/main/apply_model.ipynb

import os
import sys
from glob import glob
from pathlib import Path

import torch as pt
from model.config import config_model  # , config_data

#     from data_handler import Dataset
from model.model import Model
from src.data_encoding import (  # , categ_to_resnames, resname_to_categ
    encode_features,
    encode_structure,
    extract_topology,
)
from src.dataset import (  # , select_by_sid, select_by_interface_types
    StructuresDataset,
    collate_batch_features,
)
from src.structure import concatenate_chains  # , data_to_structure,
from src.structure import encode_bfactor, split_by_chain
from src.structure_io import save_pdb  # , read_pdb
from tqdm import tqdm

# from src.scoring import bc_scoring, bc_score_names


def main(file_dir: Path, use_gpu: bool = False) -> None:
    """
    Main function to run the PESTO workflow.
    """

    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    #     data_path = "examples/issue_20_04_2023"
    save_path = os.path.join(current_file_dir, "model/save/i_v4_1_2021-09-07_11-21")  # 91
    # select saved model
    model_filepath = os.path.join(save_path, "model_ckpt.pt")
    if save_path not in sys.path:
        sys.path.insert(0, save_path)

    device = pt.device("gpu" if use_gpu and pt.cuda.is_available() else "cpu")
    model = Model(config_model)

    model.load_state_dict(
        pt.load(model_filepath, map_location=pt.device("gpu" if use_gpu and pt.cuda.is_available() else "cpu"))
    )

    model = model.eval().to(device)

    pdb_filepaths = glob(os.path.join(file_dir, "*.pdb"), recursive=True)
    # list the content of the directory
    print(f"Contents of {file_dir}:")
    for item in os.listdir(file_dir):
        print(f" - {item}")
    print(f"Found {len(pdb_filepaths)} PDB files in {file_dir}.")
    pdb_filepaths = [fp for fp in pdb_filepaths if "_i" not in fp]

    dataset = StructuresDataset(pdb_filepaths, with_preprocessing=True)

    print(len(dataset))

    # run model on all subunits
    with pt.no_grad():
        for subunits, filepath in tqdm(dataset):
            # concatenate all chains together
            structure = concatenate_chains(subunits)
            # encode structure and features
            X, M = encode_structure(structure)
            # q = pt.cat(encode_features(structure), dim=1)
            q = encode_features(structure)[0]
            # extract topology
            ids_topk, _, _, _, _ = extract_topology(X, 64)
            # pack data and setup sink (IMPORTANT)
            X, ids_topk, q, M = collate_batch_features([[X, ids_topk, q, M]])
            # run model
            z = model(X.to(device), ids_topk.to(device), q.to(device), M.float().to(device))
            # for all predictions
            for i in range(z.shape[1]):
                # prediction
                p = pt.sigmoid(z[:, i])
                # encode result
                structure = encode_bfactor(structure, p.cpu().numpy())
                # save results
                output_filepath = filepath[:-4] + "_i{}.pdb".format(i)
                save_pdb(split_by_chain(structure), output_filepath)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run PESTO on a directory of PDB files.")
    parser.add_argument(
        "-d", "--file-dir", type=Path, required=True, help="Directory containing the PDB files to process."
    )
    parser.add_argument("--use-gpu", action="store_true", help="Whether to use GPU for processing.")

    args = parser.parse_args()
    main(args.file_dir, args.use_gpu)
