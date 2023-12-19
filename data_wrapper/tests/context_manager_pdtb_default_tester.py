import json, argparse

from data_wrapper.pdtb_data_wrapper import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_file", required=True)
    parser.add_argument("--label_file", required=True)
    args = parser.parse_args()

    print(f"testing pdtb3 file reading facility")

    # data_file = "../../data/test/wsj_2100.raw"
    # label_file = "../../data/test/wsj_2100"

    data_file = args.data_file
    label_file = args.label_file

    data = pdtb3_file_reader(data_file, label_file)

    print(f"{json.dumps(data, indent=3)}")