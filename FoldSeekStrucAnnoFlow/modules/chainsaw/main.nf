process CHAINSAW_RUN {
    tag "${input_file}"
    input:
        file input_file
        val repo_dir      // Path to repo with get_predictions.py, from config
        val work_dir      // Working directory to return to
        val extra_args    // Any extra args for get_predictions.py (optional)
        val cpu_flag      //Not sure if needed here 
        val gpu_flag 
        

    output:
        path chainsaw_output_file
        file versions_file
    
    script:
    chainsaw_output_file = "${input_file.simpleName}_chainsaw_output.txt"
    versions_file = "chainsaw_versions.yml"
    """
    orig_dir=\$(pwd)
    cd ${repo_dir} || exit 1
    extra_args="\${extra_args:-}"

    uv run --python .venv/bin/python get_predictions.py --structure_file \${orig_dir}/${input_file} -o \${orig_dir}/${chainsaw_output_file} \${extra_args}

    cat <<EOF > \${orig_dir}/$versions_file
    uv: \$(uv --version)
    python: \$(uv run --python .venv/bin/python python --version)
    EOF
  

"""

    stub:
    """
    mkdir -p output
    touch output/dummy_chainsaw.txt
    echo "uv: 0.1.0" > output/chainsaw_versions.yml
    """

}