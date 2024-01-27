import argparse, json, os, csv
import codecs
import data_wrapper.disrpt_wrapper.disrpt_to_connrel_converter as disrpt_wrapper
import data_wrapper.disrpt_wrapper.ddtb_to_connrel_converter as ddtb_wrapper

def process_dataset(disrpt_input, disrpt_dataset, output, context_mode, context_size, ddtb_input):

    #--------------------------------------------
    #read in the ddtb trees if they exist
    #--------------------------------------------
    trees = None
    final_relation_connective_mapping = None
    context_index = None
    if ddtb_input:
        trees = ddtb_wrapper.read_ddtb_trees(ddtb_input)

        # finds candidate connectives for relations empirically
        final_relation_connective_mapping = ddtb_wrapper.analyse_trees_for_relation_connectives_mappings(trees)
        print(f"{json.dumps(final_relation_connective_mapping, indent=3)}")

        context_index = ddtb_wrapper.create_context_indices(trees, context_mode=context_mode)

    #--------------------------------------------
    #read in disrpt relations (data points)
    #--------------------------------------------
    disrpt_dir_structure = disrpt_wrapper.get_disrpt_dir_structure(disrpt_dataset)

    relations = {}
    label_set = []
    docs_data = {}
    for data_split_key in disrpt_dir_structure["rels"].keys():
        pathway = disrpt_dir_structure["rels"][data_split_key]
        full_pathway = os.path.join(disrpt_input, pathway)
        # print(f"reading DISRPT rel data: {full_pathway}")
        rels, docs = disrpt_wrapper.read_disrpt_rels(full_pathway)
        relations[data_split_key] = rels
        docs_data[data_split_key] = docs

    #write data to disk
    data_set_dirname = disrpt_dataset.replace(".", "_")
    mode_dirname = f"mode-{context_mode}-context-{context_size}"
    data_mode_dir = os.path.join(output,  data_set_dirname, "withContext", mode_dirname, data_set_dirname, "fine")
    os.makedirs(data_mode_dir, exist_ok=True)

    for data_split_key in relations.keys():
        # read in the conllu files to get org text
        filename = disrpt_dir_structure["conllu"][data_split_key]
        # raw_texts = disrpt_wrapper.read_disrpt_connllu_for_raw_text(os.path.join(disrpt_input, filename))
        raw_texts = docs_data[data_split_key]

        # print(f"raw text keys: {raw_texts.keys()}")

        # print(f"data_split: {data_split_key}")
        output_data = []
        for relation in relations[data_split_key]:
            corrected = None
            # Check if this is a ddtb style set and we have the DDTB source files
            if disrpt_dataset.find(".dep.") and ddtb_input:
                corrected = disrpt_wrapper.convert(relation,
                                                    context_mode=context_mode, context_size=context_size)
            else:
                corrected = disrpt_wrapper.convert(relation, relations=relations[data_split_key],
                                                   raw_texts=raw_texts,
                                                   context_mode=context_mode, context_size=context_size)

            output_data.append(corrected)
            if not corrected["relation_class"] in label_set:
                label_set.append(corrected["relation_class"])

        with open(os.path.join(data_mode_dir, data_split_key+".json"), "w") as output_file:
            for datum in output_data:
                output_file.write(json.dumps(datum)+"\n")

    with open(os.path.join(data_mode_dir, "labels_level_1.txt"), "w") as output_file:
        for label in label_set:
            output_file.write(label+"\n")

    return data_mode_dir, data_set_dirname

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--disrpt_input", required=True)
    parser.add_argument("--ddtb_input", default=None)
    parser.add_argument("--disrpt_dataset", default="eng.dep.scidtb")
    parser.add_argument("--output", required=True)
    parser.add_argument("--context_mode", type=int, default=None, help="None:default; 0:all, 1:PDTB_gold, 2:Jeon_segments; 3:Always_last_sentence")
    parser.add_argument("--context_size", type=int, default=1)
    args = parser.parse_args()

    process_dataset(args.disrpt_input, args.disrpt_dataset,args.output,
                    args.context_mode, args.context_size, args.ddtb_input )
