import json, argparse

from data_wrapper import pdtb_context_extension
from preprocessing import  pdtb3_file_reader

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

    cur_samples = pdtb3_file_reader(data_file=data_file, label_file=label_file)
    context_mode = 1
    context_size = 1

    # extract context only if the PDTB raw text directory is provided
    cur_samples, stats = pdtb_context_extension.read_pdtb_sample(cur_samples, input_filename=label_file,
                                                                 raw_text_location=data_file,
                                                                 dataset="pdtb3",
                                                                 mode=context_mode, context_size=context_size,
                                                                 jeon_segment_reader=None,
                                                                 FLAG_prepocessing_version=3)

    print(f"{json.dumps(cur_samples, indent=3)}")