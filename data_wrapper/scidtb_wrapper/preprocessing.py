import argparse, json, os, csv
import codecs

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




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--disrpt_input", required=True)
    parser.add_argument("--scidtb_input", required=True)
    # parser.add_argument("--output", required=True)
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

    print(f"Data in SciDTB: {len(trees.keys())}")

    relation_connective_mapping = {}
    for data_split_key in ["dev", "train"]:
        for filename in trees[data_split_key].keys():
            a_tree = trees[data_split_key][filename]    # dict: { "root": [ <list of dicts> ] }
            edges = a_tree["root"]
            for edge in edges:
                if edge["text"] == "ROOT":
                    continue    #skip the root edge
                else:
                    relation = edge["relation"]
                    if not relation in relation_connective_mapping.keys():
                        relation_connective_mapping[relation] = {}
                    first_word = edge["text"].lower().split(" ")[0]     #take first word, make lowercase
                    if first_word not in relation_connective_mapping[relation].keys():
                        relation_connective_mapping[relation][first_word] = 1
                    else:
                        relation_connective_mapping[relation][first_word] += 1

    for relation in relation_connective_mapping.keys():
        hist = relation_connective_mapping[relation]
        sorted_hist = {k: v for k, v in sorted(hist.items(), key=lambda item: item[1], reverse=True)}

        for key  in sorted_hist.keys():
            filter_string = "---"
            if int(sorted_hist[key]) > 1 :
                filter_string = ""
            print(f"{relation}: {filter_string} word {key}, freq: {sorted_hist[key]}")



    #--------------------------------------------
    #read in disrpt scidtb relations
    #--------------------------------------------
    relations = {}
    for data_split_key in disrpt_dir_structure["rels"].keys():
        pathway = disrpt_dir_structure["rels"][data_split_key]
        full_pathway = os.path.join(args.disrpt_input, pathway)
        rels = read_disrpt_scidtb_rels(full_pathway)
        relations[data_split_key] = rels
