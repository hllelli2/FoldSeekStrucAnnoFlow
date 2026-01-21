process MERIZO_RUN {
    tag "${input_file}"

    input:
        file input_file
        val repo_dir      // Path to repo with predict.py, from config
        val work_dir      // Working directory to return to
        val extra_args    // Any extra args for predict.py (optional)

    output:
        file 'output/*'   // Adjust as needed for actual output files
        file 'versions.yml'

    script:
    """
    orig_dir=\$(pwd)
    cd ${repo_dir} || exit 1
    uv run python predict.py --input ${input_file} --output-dir ${work_dir}/output ${extra_args}
    cd \${orig_dir} || exit 1
    cat <<EOF > ${work_dir}/versions.yml
    uv: \$(uv --version)
    python: \$(python --version)
    EOF    
    """


    stub:
    """
    mkdir -p output
    touch output/dummy.txt
    echo "uv: 0.1.0" > versions.yml
    """

}