import argparse, json, csv, os

from pdtb_data_wrapper import read_pdtb_raw_and_labels

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="LDC PDTC2 parent directory containing raw data")
    parser.add_argument("--output", required=True, help="where to write output CSV files to")
    parser.add_argument("--dataset", default="pdtb2", help="specifies the version of the PDTB data set (2 vs 3)")

    args = parser.parse_args()

    #clear output
    output_filenames = ["train.csv", "test.csv", "dev.csv"]
    for filename in output_filenames :
        try:
            os.remove(os.path.join(args.output, filename))
        except OSError:
            pass

    #create new output

    for filename in output_filenames:
        output_path = os.path.join(args.output, filename)
        with open(output_path, 'a', newline='') as csvfile:
            fieldnames = ['essay_id', 'prompt', 'native_lang', 'essay_score', 'essay']
            writer = csv.writer(csvfile)
            writer.writerow(fieldnames)

    file_extension =".pdtb"
    if args.dataset == "pdtb3":
        file_extension = ""

    #read raw data
    data, raw_text, processed_files = read_pdtb_raw_and_labels(args.input, file_extension=file_extension,
                                                               dataset=args.dataset)
    # print(f"data_size: {len(data)}, raw_text_size: {len(raw_text)}, processed_files: {processed_files}")

    test = ["21", "22"]
    dev = ["00","01"]
    for i, filename in enumerate(processed_files):
        filename_parts = filename.split("/")
        id = None
        if args.dataset=="pdtb2":
            id = filename_parts[-1][len("wsj_"):-len(file_extension)]  #strip off the file extension and "wsj_" prefix
        else:
            id = filename_parts[-1][len("wsj_"):]  # strip off the file extension and "wsj_" prefix

        # print(f"{filename_parts[-1]}, {id}")
        id_sect = id[:2]
        id_file = id[2:]
        # print(f"{id_sect}, {id_file}")

        output_filename = "train.csv"
        if id_sect in test:
            output_filename = "test.csv"
        if id_sect in dev:
            output_filename = "dev.csv"
        output_path = os.path.join(args.output, output_filename)
        with open(output_path, 'a', newline='') as csvfile:
            fieldnames = ['essay_id', 'prompt', 'native_lang', 'essay_score', 'essay']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not os.path.exists(output_path):
                writer.writeheader()

            #write row for this pdtb file
            writer.writerow({'essay_id':id, 'prompt':1, 'native_lang': "ENG", 'essay_score': 1, 'essay':raw_text[i]})