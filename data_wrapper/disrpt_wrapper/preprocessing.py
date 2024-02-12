import argparse, json, os, csv
import codecs
import data_wrapper.disrpt_wrapper.disrpt_to_connrel_converter as disrpt_wrapper
import data_wrapper.disrpt_wrapper.ddtb_to_connrel_converter as ddtb_wrapper
import data_wrapper.disrpt_wrapper.resources as disrpt_resources
from data_wrapper.context_manager_joen import ContextManagerJoen


def process_dataset(disrpt_input, disrpt_dataset, output, context_mode, context_size, ddtb_input,
                    jeon_segment_reader=None):

    #prepare variables/directories for output
    data_set_dirname = disrpt_dataset.replace(".", "_")
    mode_dirname = f"mode-{context_mode}-context-{context_size}"
    data_mode_dir = os.path.join(output,  data_set_dirname, "withContext", mode_dirname)
    data_final_output = os.path.join(data_mode_dir, data_set_dirname, "fine")
    os.makedirs(data_final_output, exist_ok=True)

    #--------------------------------------------
    #read in the ddtb trees if they exist
    #--------------------------------------------
    trees = {}
    final_relation_connective_mapping = None
    context_index = None
    FLAG_ddtb_tree_data_exists = False
    if ddtb_input and \
        disrpt_dataset in disrpt_resources.ddtb_datasets.keys(): # reality check, is a dep dataset?
        trees = ddtb_wrapper.read_ddtb_trees(ddtb_input=ddtb_input, dataset_name=disrpt_dataset)
        print(f"Using DDTB dependency data")
        FLAG_ddtb_tree_data_exists = True

    #--------------------------------------------
    #read in disrpt relations (data points)
    #--------------------------------------------
    print(f"Processing relations.")
    disrpt_dir_structure = disrpt_wrapper.get_disrpt_dir_structure(disrpt_dataset)

    relations = {}
    label_set = []
    docs_data = {}

    for data_split_key in disrpt_dir_structure["rels"].keys():
        pathway = disrpt_dir_structure["rels"][data_split_key]
        full_pathway = os.path.join(disrpt_input, pathway)
        # print(f"reading DISRPT rel data: {full_pathway}")
        rels, docs, trees_data = disrpt_wrapper.read_disrpt_rels(full_pathway)
        relations[data_split_key] = rels
        docs_data[data_split_key] = docs
        if not FLAG_ddtb_tree_data_exists:
            trees[data_split_key] = trees_data

    #--------------------------------------------
    # Process the trees, whereever they came from (DDTB or DISRPT rel data)
    #--------------------------------------------
    # finds candidate connectives for relations empirically
    final_relation_connective_mapping = ddtb_wrapper.analyse_trees_for_relation_connectives_mappings(trees)
    connective_mapping_str = f"{json.dumps(final_relation_connective_mapping, indent=3)}"
    # print(connective_mapping_str)

    with open(os.path.join(data_final_output, "final_relation_connective_mapping.json"), "w") as output_file:
        output_file.write(connective_mapping_str)
    context_index = None
    if context_mode:
        context_index = ddtb_wrapper.create_context_indices(trees, context_mode=context_mode)

    #convert data and write data to disk
    saved_docid_mapping = {}  # need to transform docids to unique ints. This saves mapping for the JEON data
    for d, data_split_key in enumerate(relations.keys()):
        # read in the conllu files to get org text
        filename = disrpt_dir_structure["conllu"][data_split_key]
        # raw_texts = disrpt_wrapper.read_disrpt_connllu_for_raw_text(os.path.join(disrpt_input, filename))
        raw_texts = docs_data[data_split_key]

        # print(f"raw text keys: {raw_texts.keys()}")

        # print(f"data_split: {data_split_key}")
        output_data = []
        saved_docids = []   #putting this inside the data_split loop because some data sets share dev==train split
        for i, relation in enumerate(relations[data_split_key]):
            corrected = None
            # Check if this is a ddtb style set and we have the DDTB source files
            if context_mode and int(context_mode)==1:            #using int() to generalise to major version
                # if disrpt_dataset.find(".dep.")>-1 and ddtb_input:
                #     # print(f"dataset: {disrpt_dataset}")
                #     corrected = ddtb_wrapper.convert(relation, context_index=context_index[data_split_key],
                #                                      context_mode=context_mode, context_size=context_size,
                #                                      _filtered_conns=final_relation_connective_mapping,
                #                                      dataset_name=disrpt_dataset)
                # else:

                corrected = ddtb_wrapper.convert(relation, context_index=context_index[data_split_key],
                                                 context_mode=context_mode, context_size=context_size,
                                                 _filtered_conns=final_relation_connective_mapping,
                                                 dataset_name=disrpt_dataset)
            elif context_mode and context_mode==2:
                context_manager = ContextManagerJoen(jeon_segment_reader)
                corrected = disrpt_wrapper.convert(relation, relations=relations[data_split_key],
                                                   raw_texts=raw_texts,
                                                   context_mode=context_mode, context_size=context_size)
                doc_id = corrected["doc"]
                arg1 = corrected["arg1"]
                corrected = context_manager.add_context_single_datapoint(doc_id=doc_id, annotation=corrected, arg1=arg1,
                                                             context_mode=context_mode)
            elif context_mode and context_mode == 3:
                corrected = disrpt_wrapper.convert(relation, relations=relations[data_split_key],
                                                   raw_texts=raw_texts,
                                                   context_mode=context_mode, context_size=context_size)
                corrected["conn"] = "[]"


            else:
                corrected = disrpt_wrapper.convert(relation, relations=relations[data_split_key],
                                                   raw_texts=raw_texts,
                                                   context_mode=context_mode, context_size=context_size)

                corrected["arg1"] = " ... "+ relation["unit1_txt"]
                # corrected["arg2"] = relation["unit2_txt"]
                corrected["conn"] = "[]"

            output_data.append(corrected)
            if not corrected["relation_class"] in label_set:
                label_set.append(corrected["relation_class"])

        with open(os.path.join(data_final_output, data_split_key+".json"), "w") as output_file:
            for datum in output_data:
                output_file.write(json.dumps(datum)+"\n")

        #write raw text (from REL data) as CSV files
        #header needs to be the fields expected by Jeon's code, in future make this generic
        csv_data_output_filename = f"{data_split_key}.jeon.csv"
        csv_data_output_path = os.path.join(data_final_output, csv_data_output_filename )

        with open(csv_data_output_path, 'w', newline='', encoding="utf-8") as csvfile:
            fieldnames = ['essay_id', 'prompt', 'native_lang', 'essay_score', 'essay']
            #essay_ids need to be some kind of int.
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for datum in output_data:
                doc_id = datum["doc"]
                if not doc_id in saved_docids:
                    saved_docids.append(doc_id)
                    new_id = d*10000+len(saved_docids)      #use data split as leading offset, assume <10k docs per split
                    saved_docid_mapping[new_id] = doc_id
                    #write row for this file
                    doc = raw_texts[doc_id]
                    doc_text = [s['sent'] for s in doc]
                    writer.writerow({'essay_id':new_id, 'prompt':1, 'native_lang': "ENG", 'essay_score': 1, 'essay':" ".join(doc_text) })

    #print labels
    with open(os.path.join(data_final_output, "labels_level_1.txt"), "w") as output_file:
        for label in label_set:
            output_file.write(label+"\n")
    with open(os.path.join(data_final_output, "docid_mapping_jeon.json"), "w") as output_file:
        output_file.write(json.dumps(saved_docid_mapping, indent=3))

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
