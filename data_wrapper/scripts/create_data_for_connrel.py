import argparse, os
import json

import data_wrapper.disrpt_wrapper.preprocessing as prep

template = """#! /usr/bin/env bash
#BATCH --job-name=WANSN-ConnRel-__DATASET__-__MODE__-__SIZE__
#SBATCH --output=/hits/basement/nlp/wansn/out/slurm/%j.out
#SBATCH --error=/hits/basement/nlp/wansn/out/slurm/%j.out
#SBATCH --time=23:59:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --partition=ice-deep.p

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=stephen.wan@h-its.org

#script

. activate ConnRel_icedeep

cd ~/work/code/wei-liu/ConnRel



for seed in 106524 106464 106537 219539 430683 420201 421052 250120 521002 105202
do
    time python3 train_joint_conn_rel.py --do_train \\
                                    --dataset=__DATASET__ \\
                                    --label_file="labels_level___LABEL_LEVEL__.txt" \\
                                    --sample_k=100 \\
                                    --seed=${seed} \\
                                    --relation_type="implicit" \\
                                    --write_file=1 \\
                                    --write_filestub="run-" \\
                                    --data_dir="__HOME____DATALOC__"
done


echo "script finished"
date

"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--disrpt_input", required=True)
    parser.add_argument("--ddtb_input", default=None)
    parser.add_argument("--output", required=True)
    parser.add_argument("--home", default="")
    parser.add_argument("--modes", default="[-1, 1,3]", help="json string of list of modes e.g., None, 1,2,3")
    parser.add_argument("--sizes", default="[1]", help="json string of list of sizes e.g., 1,2,3")
    parser.add_argument("--label_levels", default="[1]", help="json string of list of label level 1,2,3")
    args = parser.parse_args()

    datasets = [
        "eng.dep.covdtb",
        "eng.dep.scidtb",
        "eng.rst.gum"
    ]

    print(f"args: {args}")

    modes = json.loads(args.modes)
    for i,mode in enumerate(modes):
        if mode==-1:
            modes[i] = None
    sizes = json.loads(args.sizes)
    label_levels = json.loads(args.label_levels)   #these are not zero-indexed! Careful, functions like ddtb_wrapper.convert expect 0-indexed level.

    for dataset in datasets:
        for mode in modes:
            for size in sizes:
                for label_level in label_levels:
                    print(f"Processing: {dataset} for mode: {mode} size: {size}")
                    dataloc, data_name = prep.process_dataset(args.disrpt_input, dataset, args.output,
                                                              mode, size, ddtb_input=args.ddtb_input)

                    slurm_script = template
                    slurm_script = slurm_script.replace("__DATALOC__", dataloc)
                    slurm_script = slurm_script.replace("__DATASET__", data_name)
                    slurm_script = slurm_script.replace("__MODE__", str(mode))
                    slurm_script = slurm_script.replace("__SIZE__", str(size))
                    slurm_script = slurm_script.replace("__LABEL_LEVEL__", str(label_level))
                    slurm_script = slurm_script.replace("__HOME__", args.home)

                    slurm_script_dir = os.path.join(args.output, "slurm")
                    os.makedirs(slurm_script_dir, exist_ok=True)
                    script_name = f"connrel-{data_name}-implicit-mode-{mode}-context-{size}-l{label_level}-icedeep.slurm"
                    with open(os.path.join(slurm_script_dir, script_name), "w") as f:
                        f.write(slurm_script)
