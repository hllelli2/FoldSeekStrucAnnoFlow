process MERIZO_RUN {
    tag "${input_file}"
    input:
        file input_file
        val repo_dir      // Path to repo with predict.py, from config
        val work_dir      // Working directory to return to
        val extra_args    // Any extra args for predict.py (optional)
        val cpu_flag
        val gpu_flag 
        

    output:
        path "${prefix}*"
        file versions_file

    script:
    prefix = "${input_file.simpleName}"
    versions_file = "merizo_versions.yml"
    """

    
    orig_dir=\$(pwd)
    cd ${repo_dir} || exit 1

    extra_args="\${extra_args:-}"
    
    # if cpu_flag is true, add -d cpu
    if [ "${cpu_flag}" = "true" ]; then
        extra_args="\${extra_args} -d cpu"
    fi
    if [ "${gpu_flag}" = "true" ]; then
        extra_args="\${extra_args} -d cuda"
    fi

    uv run --python .venv/bin/python predict.py -i \${orig_dir}/${input_file} --save_domains \${extra_args}

    cat <<EOF > \${orig_dir}/$versions_file
    uv: \$(uv --version)
    python: \$(uv run --python .venv/bin/python python --version)
    EOF
    
    """


    stub:
    """
    mkdir -p output
    touch output/dummy.txt
    echo "uv: 0.1.0" > output/merizo_versions.yml
    """

}