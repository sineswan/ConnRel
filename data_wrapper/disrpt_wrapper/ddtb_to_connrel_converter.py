import os, json
from data_wrapper.disrpt_wrapper.resources import filtered_connectives as manual_filtered_conns, dataset_file_extensions
import data_wrapper.disrpt_wrapper.disrpt_to_connrel_converter as disrpt_wrapper

default_connective = "and"

def pick_conn(label, filtered_conns):
    a_dict = filtered_conns[label]
    sorted_hist = {k: v for k, v in sorted(a_dict.items(), key=lambda item: item[1], reverse=True)}
    result = default_connective  #default
    for key in sorted_hist.keys():
        #should be sorted by freq/value, so take 1st key
        result = key
        break
    return result


def convert(relation, context_index=None,  context_mode=None,
            context_size=0, label_level=0, _filtered_conns=None, dataset_name=None):
    """

    Args:
        relation:
        context_index: a dicts.  "context" key is an ordered array of context records for this relation
        context_mode:
        context_size:
        dataset_fileext:

    Returns:

    """
    result = disrpt_wrapper.convert(relation, context_mode, context_size, label_level)
    id = f"{relation['doc']}.{relation['unit1_toks']}.{relation['unit2_toks']}"
    arg1 = relation["unit1_txt"]
    arg2 = relation["unit2_txt"]
    label = relation["label"]
    filename = relation["doc"]
    dataset_fileext = dataset_file_extensions[dataset_name]

    #find context
    if context_mode:
        if context_mode==1:
            context_record = None
            provenance = None
            if context_index:
                an_index = context_index[filename+dataset_fileext]
                context = ""

                #Modification 2024.02.04: adding filter to remove self relation
                rejected = None
                arg1_key_target = arg1.strip()
                if arg1_key_target in an_index.keys():
                    provenance = an_index[arg1_key_target]
                    context_record = provenance["context"][0]
                    if context_record:
                        candidate = context_record["text"]

                        # Modification 2024.02.04: adding filter to remove self relation
                        if not candidate.strip() == arg2.strip():
                            context == candidate
                        else:
                            rejected = context_record
                            print(f"Data[{id}]: rejecting context as self: {rejected}")

                if context=="":
                    # no exact match, have to use fuzzy matching
                    for key in an_index.keys():
                        if arg1_key_target.startswith(key) or key.startswith(arg1_key_target):
                            provenance = an_index[key]
                            context_record = provenance["context"][0]
                            if context_record:
                                if not context_record == rejected:
                                    context = context_record["text"]
                                    print(f"Data[{id}]: fuzzy match: {context}")
                                    break
                    if context == "": #still empty
                        print(f"WARNING: Empty context for {id}, arg1: {arg1}")

                result["arg1"] = context + " ... " + arg1
                result["context"] = context
                result["context_provenance"] = provenance

            #determine connective
            conn = disrpt_wrapper.get_first_word(arg2)
            alt_arg2 = disrpt_wrapper.get_tail(arg2)
            filtered_conns = _filtered_conns
            if dataset_name in manual_filtered_conns.keys():
                filtered_conns = manual_filtered_conns[dataset_name]
                # print(f"Using manual filtered connectives mapping for {dataset_name}")
            if label in filtered_conns.keys():      #need to parameterise filtered_conns
                # print(f"DEBUG: found label: {label}")
                if conn.lower() in filtered_conns[label].keys():
                    #this conn is in the vetted list, so use it, and pop it from arg2 (==alt_arg2)
                    result["arg2"] = alt_arg2
                else:
                    #this conn is NOT in vetted list, pick another from the vetted list
                    #keep arg2 as it is
                    conn = pick_conn(label, filtered_conns)
            else:
                #Try the "generic" filtered connectives in the manual resource
                general_filtered_conns = manual_filtered_conns["general"]
                if label in general_filtered_conns.keys():
                    if conn.lower() in general_filtered_conns[label].keys():
                        # this conn is in the vetted list, so use it, and pop it from arg2 (==alt_arg2)
                        result["arg2"] = alt_arg2
                    else:
                        # this conn is NOT in vetted list, pick another from the vetted list
                        # keep arg2 as it is
                        conn = pick_conn(label, general_filtered_conns)
                else:
                    print(f"WARNING: Missing label: {label}")
                    conn = default_connective

            if conn==None or conn=="":
                print(f"ERROR!: Conn: {conn}, relation: {relation}")
                conn = default_connective
            # else:
            #     print(f"Conn: {conn}")

            result["conn"] = conn

    # print(f"result: {json.dumps(result, indent=3)}")

    return result

def read_ddtb_trees(ddtb_input, dataset_name):

    trees = {
        "dev":{},
        "train":{},
        "test":{}
    }

    ddtb_dir_structure = None
    if dataset_name=="eng.dep.scidtb":
        ddtb_dir_structure = {
            "dev": f"{dataset_name}/dev/gold",
            "test": f"{dataset_name}/test/gold",
            "train": f"{dataset_name}/train"
        }
    elif dataset_name=="eng.dep.covdtb":
        ddtb_dir_structure = {
            "dev": f"{dataset_name}/dev",
            "test": f"{dataset_name}/test",
            "train": None
        }

    for data_split_key in trees.keys():
        pathway = ddtb_dir_structure[data_split_key]
        if pathway:
            full_pathway = os.path.join(ddtb_input, pathway)
            for filename in sorted(os.listdir(full_pathway)):
                tree_info = read_ddtb_dep_file(os.path.join(full_pathway, filename))
                trees[data_split_key][filename] = tree_info

                # print(f"tree: {json.dumps(tree_info, indent=3)}")
    return trees

def read_ddtb_dep_file(filename):
    file_contents = open(filename, "r", encoding="utf-8-sig").read()
    # print(f"File_contents: {file_contents}")
    return json.loads(file_contents)


def create_context_indices(trees, context_mode=1):
    """
    Args:
        trees:
        context_mode:

    Returns: an dict of records, "self" is the data point, "context" is an array of the
    preceding context records, ordered so that the immediate parent is 1st and going down array goes up ancestry.

    """

    #ANALYSE relation-first_word mappings
    index = {}
    for data_split_key in ["dev", "train", "test"]:
        index[data_split_key] = {}
        for filename in trees[data_split_key].keys():
            a_tree = trees[data_split_key][filename]    # dict: { "root": [ <list of dicts> ] }
            edges = a_tree["root"]
            edge_lookup = {}
            for edge in edges:
                edge_id = edge["id"]
                edge_lookup[edge_id] = edge

            reverse_index = {}
            for edge in edges:
                edge_id = None
                # if "-" in edge["id"]:
                #     edge_id = int(edge["id"].replace("-", ""))
                # else:
                edge_id = int(edge["id"])
                edge["text"] = edge["text"].replace("<S>", "").strip()
                text = edge["text"]
                parent_edge_id = edge["parent"]

                context = None
                if context_mode==1:
                    if parent_edge_id > -1:     #this currently doesn't do anything, since -1 isn't used, 0 is actual root
                        context = edge_lookup[parent_edge_id]
                        context["text"] = context["text"].replace("<S>", "")
                # elif context_mode==3:
                #     if edge_id > 1:
                #         prev_id = edge_id - 1
                #         context = edge_lookup[prev_id]

                reverse_index[text] = {"self":edge, "context":[context]}
            index[data_split_key][filename] = reverse_index

    return index

def vet_word(word):
    if word in ["(", ")", ".", "!", "?", "-"]:
        return None
    return word

def analyse_trees_for_relation_connectives_mappings(trees):

    print(f"trees keys: {trees.keys()}")

    #ANALYSE relation-first_word mappings
    relation_connective_mapping = {}
    for data_split_key in ["dev", "train"]:
        for filename in trees[data_split_key].keys():
            a_tree = trees[data_split_key][filename]    # dict: { "root": [ <list of dicts> ] }

            # print(f"a_tree: {json.dumps(a_tree, indent=3)}")

            edges = a_tree["root"]
            for edge in edges:
                if edge["text"] == "ROOT":
                    continue    #skip the root edge
                elif not int(edge["parent"]) == (int(edge["id"]) - 1):  #only analyse cases where parent directly precedes
                    continue
                else:
                    relation = edge["relation"].lower()
                    if not relation in relation_connective_mapping.keys():
                        relation_connective_mapping[relation] = {}
                    first_word = edge["text"].lower().split(" ")[0]     #take first word, make lowercase
                    filtered_word = vet_word(first_word)
                    if filtered_word:
                        if filtered_word not in relation_connective_mapping[relation].keys():
                            relation_connective_mapping[relation][filtered_word] = 1
                        else:
                            relation_connective_mapping[relation][filtered_word] += 1

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
            # print(f"{relation}: {filter_string} word= {key}, freq= {sorted_hist[key]}")
        final_relation_connective_mapping[relation] = filtered_connectives

    return final_relation_connective_mapping