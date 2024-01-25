import argparse, json, os, csv
import codecs
import scidtb_to_connrel_converter

def read_scidtb_trees(filename):
    file_contents = open(filename, "r", encoding="utf-8-sig").read()
    # print(f"File_contents: {file_contents}")
    return json.loads(file_contents)

def read_disrpt_scidtb_rels(filename):
    # open .tsv file
    data = []
    with open(filename) as file:
        csv_reader = csv.DictReader(file, delimiter="\t")
        for row in csv_reader:
            # print(row)
            data.append(row)
    return(data)

def analyse_trees_for_relation_connectives_mappings(trees):


    #ANALYSE relation-first_word mappings
    relation_connective_mapping = {}
    for data_split_key in ["dev", "train"]:
        for filename in trees[data_split_key].keys():
            a_tree = trees[data_split_key][filename]    # dict: { "root": [ <list of dicts> ] }
            edges = a_tree["root"]
            for edge in edges:
                if edge["text"] == "ROOT":
                    continue    #skip the root edge
                elif not int(edge["parent"]) == (int(edge["id"]) - 1):  #only analyse cases where parent directly precedes
                    continue
                else:
                    relation = edge["relation"]
                    if not relation in relation_connective_mapping.keys():
                        relation_connective_mapping[relation] = {}
                    first_word = edge["text"].lower().split(" ")[0]     #take first word, make lowercase
                    if first_word not in relation_connective_mapping[relation].keys():
                        relation_connective_mapping[relation][first_word] = 1
                    else:
                        relation_connective_mapping[relation][first_word] += 1

    final_relation_connective_mapping = {}
    for relation in relation_connective_mapping.keys():
        hist = relation_connective_mapping[relation]
        sorted_hist = {k: v for k, v in sorted(hist.items(), key=lambda item: item[1], reverse=True)}

        filtered_connectives = {}
        for key  in sorted_hist.keys():
            filter_string = "---"
            if int(sorted_hist[key]) > 1 :
                filter_string = ""
                filtered_connectives[key] = sorted_hist[key]
            print(f"{relation}: {filter_string} word= {key}, freq= {sorted_hist[key]}")
        final_relation_connective_mapping[relation] = filtered_connectives

    return final_relation_connective_mapping


def create_context_indices(trees, context_mode=1):

    #ANALYSE relation-first_word mappings
    index = {}
    for data_split_key in ["dev", "train", "test"]:
        index[data_split_key] = {}
        for filename in trees[data_split_key].keys():
            a_tree = trees[data_split_key][filename]    # dict: { "root": [ <list of dicts> ] }
            edges = a_tree["root"]
            edge_lookup = {}
            for edge in edges:
                text = edge["text"]
                edge_id = edge["id"]
                edge_lookup[edge_id] = edge

            reverse_index = {}
            for edge in edges:
                edge_id = int(edge["id"])
                text = edge["text"].replace("<S>", "").strip()
                parent_edge_id = edge["parent"]

                context = None
                if context_mode==1:
                    if parent_edge_id > -1:
                        context = edge_lookup[parent_edge_id]
                elif context_mode==3:
                    if edge_id > 1:
                        prev_id = edge_id - 1
                        context = edge_lookup[prev_id]

                reverse_index[text] = context
            index[data_split_key][filename] = reverse_index

    return index


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--disrpt_input", required=True)
    parser.add_argument("--scidtb_input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--context_mode", type=int, default=None, help="None:default; 0:all, 1:PDTB_gold, 2:Jeon_segments; 3:Always_last_sentence")
    parser.add_argument("--context_size", type=int, default=1)
    args = parser.parse_args()


    scidtb_dir_structure = {
    "dev":"dataset/dev/gold",
    "test":"dataset/test/gold",
    "train":"dataset/train"
    }

    disrpt_subdataset = "eng.dep.scidtb"
    disrpt_dir_structure = {
        "tokens": {
            "dev":f"{disrpt_subdataset}/{disrpt_subdataset}_dev.tok",
            "test":f"{disrpt_subdataset}/{disrpt_subdataset}_test.tok",
            "train":f"{disrpt_subdataset}/{disrpt_subdataset}_train.tok"
        },
        "conllu": {
            "dev":f"{disrpt_subdataset}/{disrpt_subdataset}_dev.conllu",
            "test":f"{disrpt_subdataset}/{disrpt_subdataset}_test.conllu",
            "train":f"{disrpt_subdataset}/{disrpt_subdataset}_train.conllu"
        },
        "rels": {
            "dev":f"{disrpt_subdataset}/{disrpt_subdataset}_dev.rels",
            "test":f"{disrpt_subdataset}/{disrpt_subdataset}_test.rels",
            "train":f"{disrpt_subdataset}/{disrpt_subdataset}_train.rels"
        }
    }


    #--------------------------------------------
    #read in the scidtb trees
    #--------------------------------------------
    trees = {
        "dev":{},
        "train":{},
        "test":{}
    }
    for data_split_key in scidtb_dir_structure.keys():
        pathway = scidtb_dir_structure[data_split_key]
        full_pathway = os.path.join(args.scidtb_input, pathway)
        for filename in sorted(os.listdir(full_pathway)):
            tree_info = read_scidtb_trees(os.path.join(full_pathway, filename))
            trees[data_split_key][filename] = tree_info

            # print(f"tree: {json.dumps(tree_info, indent=3)}")

    final_relation_connective_mapping = analyse_trees_for_relation_connectives_mappings(trees)        #finds candidate connectives for relations empirically
    print(f"{json.dumps(final_relation_connective_mapping, indent=3)}")

    context_index = create_context_indices(trees, context_mode=args.context_mode)

    #--------------------------------------------
    #read in disrpt scidtb relations (data points)
    #--------------------------------------------
    relations = {}
    label_set = []
    for data_split_key in disrpt_dir_structure["rels"].keys():
        pathway = disrpt_dir_structure["rels"][data_split_key]
        full_pathway = os.path.join(args.disrpt_input, pathway)
        rels = read_disrpt_scidtb_rels(full_pathway)
        relations[data_split_key] = rels

    for data_split_key in relations.keys():
        print(f"data_split: {data_split_key}")
        output_data = []
        for relation in relations[data_split_key]:
            corrected = scidtb_to_connrel_converter.convert(relation, context_index[data_split_key],
                                                            context_mode=args.context_mode, context_size=args.context_size)
            output_data.append(corrected)

            if not corrected["relation_class"] in label_set:
                label_set.append(corrected["relation_class"])

        with open(os.path.join(args.output, data_split_key+".json"), "w") as output_file:
            for datum in output_data:
                output_file.write(json.dumps(datum)+"\n")

    with open(os.path.join(args.output, "labels_level_1.txt"), "w") as output_file:
        for label in label_set:
            output_file.write(label+"\n")