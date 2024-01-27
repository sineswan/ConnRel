import argparse
import data_wrapper.disrpt_wrapper.preprocessing as prep

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--disrpt_input", required=True)
    parser.add_argument("--ddtb_input", default=None)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    datasets = [
        "eng.dep.covdtb",
        "eng.dep.scidtb",
        "eng.rst.gum"
    ]

    modes = [None, 3]
    sizes = [1]

    for dataset in datasets:
        for mode in modes:
            for size in sizes:
                print(f"Processing: {dataset} for mode: {mode} size: {size}")
                prep.process_dataset(args.disrpt_input, dataset, args.output, mode, size, ddtb_input=None)
