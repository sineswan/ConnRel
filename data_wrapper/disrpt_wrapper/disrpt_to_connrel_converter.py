import argparse, json, csv, os
import math

def get_disrpt_dir_structure(disrpt_subdataset):
    disrpt_dir_structure = {
        "tokens": {
            "dev": f"{disrpt_subdataset}/{disrpt_subdataset}_dev.tok",
            "test": f"{disrpt_subdataset}/{disrpt_subdataset}_test.tok",
            "train": f"{disrpt_subdataset}/{disrpt_subdataset}_train.tok"
        },
        "conllu": {
            "dev": f"{disrpt_subdataset}/{disrpt_subdataset}_dev.conllu",
            "test": f"{disrpt_subdataset}/{disrpt_subdataset}_test.conllu",
            "train": f"{disrpt_subdataset}/{disrpt_subdataset}_train.conllu"
        },
        "rels": {
            "dev": f"{disrpt_subdataset}/{disrpt_subdataset}_dev.rels",
            "test": f"{disrpt_subdataset}/{disrpt_subdataset}_test.rels",
            "train": f"{disrpt_subdataset}/{disrpt_subdataset}_train.rels"
        }
    }

    #Exceptions
    if disrpt_subdataset=="eng.dep.covdtb":
        disrpt_dir_structure["rels"]["train"] = f"{disrpt_subdataset}/{disrpt_subdataset}_dev.rels"

    return disrpt_dir_structure

def make_dep_node(datum):

    processed_ids = []      #ordering matters
    # fix commas, single num offset
    for id_string in [datum["unit2_toks"],datum["unit1_toks"]]:
        processed_result = None
        if "," in id_string:
            spans = id_string.split(",")
            first_start = spans[0]  #assume no "-" to initialise
            if "-" in spans[0]:
                first_start, _ = spans[0].split("-")
            last_end = spans[-1]
            if "-" in spans[-1]:
                _, last_end = spans[-1].split("-")
            processed_result = "{:04d}".format(int(first_start))+"-"+"{:04d}".format(int(last_end))
        elif "-" in id_string:
            # not multiples spans but could have offsets

            offsets = id_string.split("-")
            processed_result = "{:04d}".format(int(offsets[0])) + "-" + "{:04d}".format(int(offsets[1]))
        else:
            #not "-" in id_string and not "," in id_string:
            processed_result = "{:04d}".format(int(id_string))+"-"+"{:04d}".format(int(id_string))
        processed_ids.append(processed_result)

    node_id = processed_ids[0]  #for code above, it's the first element
    parent_id = processed_ids[1] #for code above, it's the second element
    node = {
        "id": node_id,
        "parent": parent_id,
        "text": datum["unit2_txt"],
        "relation": datum["label"],
        "doc": datum["doc"]
    }

    parent_node = {
        "id": parent_id,
        "parent": "0000-0000",
        "text": datum["unit1_txt"],
        "comment": "originally linked to ROOT",
        "relation": "ROOT",
        "doc": datum["doc"]
    }

    # for an_id_str in [node_id, parent_id]:
    #     if not "-" in an_id_str:
    #         print(f"ERROR in id creation. Node: {json.dumps(node, indent=3)}")
    #         print(f"ERROR in id creation. Parent: {json.dumps(parent_node, indent=3)}")
    #         1/0

    return node, parent_node

def make_doc_node_list(nodes, possible_parents):
    missing_parents_count = 0
    found_parents_count = 0

    #check dep structure for missing parents
    missing_parents = {}
    for node_id in nodes.keys():
        node = nodes[node_id]
        parent_id = node["parent"]
        if not parent_id  in nodes.keys():
            # print(f"Missing parent: {parent_id}")
            missing_parents_count += 1

            default_parent = possible_parents[parent_id]
            parent_id_parts = parent_id.split("-")  #should only be 2 given the processing in make_dep_node()
            parent_start = int(parent_id_parts[0])
            parent_end = int(parent_id_parts[1])

            #see if we can update the grandparent information
            candidate_gparents = {}
            FLAG_found_grandparent = False
            for g_node_id in nodes.keys():
                g_node = nodes[g_node_id]
                node_id_parts = g_node_id.split("-")  #should only be 2 given the processing in make_dep_node()
                g_node_start = int(node_id_parts[0])
                g_node_end = int(node_id_parts[1])
                if parent_start >= g_node_start and parent_end <= g_node_end:       #so parent is subsumed by gnode
                    # print(f"found missing parent: {g_node_id}")
                    FLAG_found_grandparent = True

                    a_score = abs(parent_start-g_node_start) + abs(parent_end-g_node_end)
                    if not a_score in candidate_gparents.keys():
                        candidate_gparents[a_score] = {}
                    candidate_gparents[a_score][g_node_start] = g_node

            if FLAG_found_grandparent:
                found_parents_count += 1

                #find best candidate parent (minimal span diff)
                best_score = min(candidate_gparents.keys())
                best_gparent_start = min(candidate_gparents[best_score].keys())
                best_gparent = candidate_gparents[best_score][best_gparent_start]
                default_parent["parent"] = best_gparent["parent"]
                default_parent["relation"] = best_gparent["relation"]

            missing_parents[parent_id] = default_parent
    #
    # print(f"Doc missing parents: {missing_parents_count}")
    # print(f"Doc found parents: {found_parents_count},{found_parents_count/missing_parents_count*100}%")
    # lost_count = missing_parents_count - found_parents_count
    # print(f"Doc lost parents: {lost_count},{lost_count/missing_parents_count*100}%")

    #now merge nodes and missing parents
    all_nodes = {**nodes, **missing_parents}        #union of dicts (should be disjoint given processing above)

    tree = {"root":[
        {
            "id": 0,
            "parent": -1,
            "text": "ROOT",
            "relation": "null"
        }
    ]}

    #give node numbers to nodes
    node_id_index = {"0000-0000":0}         #zero is the root
    for i,node_id in enumerate(sorted(all_nodes.keys())):
        node_id_index[node_id] = i+1        #zero is the root, so increment: +1

    #adjust node record for new node ids
    for i, node_id in enumerate(sorted(all_nodes.keys())):
        a_node = all_nodes[node_id]
        parent_span = a_node["parent"]
        a_node["span"] = node_id
        a_node["parent_span"] = parent_span
        a_node["id"] = node_id_index[node_id]
        new_parent_id = node_id_index[parent_span]
        a_node["parent"] = new_parent_id
        tree["root"].append(a_node)

    stats = {
        "found_parents_count":found_parents_count,
        "missing_parents_count":missing_parents_count
    }

    return tree, stats

def read_disrpt_rels(filename):
    # open .tsv file
    data = []
    docs = {}  #key=doc_id, val=[{"sent":<str>, "id":<str>} ... ]
    trees = {}  #key=doc_id, val:dict (following scidtb json structure)

    #Read the relations
    if not os.path.exists(filename):
        print(f"WARNING file not found: {filename}")

        return data, docs, trees
    else:
        with open(filename, encoding="utf-8") as file:

            #read in all the lines, and fix any \t" (tab followed by double quote) errors
            data_lines = file.readlines()
            corrected_lines = []
            for line in data_lines:
                corrected_line = line.replace("\t\"", "\t\\\"")
                # if corrected_line != line:
                #     print(f"corrected line: {corrected_line}")
                corrected_lines.append(corrected_line)

            csv_reader = csv.DictReader(corrected_lines, delimiter="\t", quoting=csv.QUOTE_ALL)
            for row in csv_reader:
                id = f"{row['doc']}.{row['unit1_toks']}.{row['unit2_toks']}"
                # print(f"id: {id}")
                # print(row)
                data.append(row)

    #Read the full text and also build up a dep node record
    sentences_tmp = {} #key=start_pos, val=sentence
    nodes_tmp = {} #key=node id, value =node (following the scidtb json structure)
    possible_parents_tmp = {}   #key=node id, value =node (following the scidtb json structure)
    last_doc_id = ""

    #variables for inferring dependency structure
    missing_parents_count = 0
    found_parents_count = 0
    for datum in data:
        doc_id = datum["doc"]

        if not doc_id == last_doc_id:
            #change in doc_id, so store the last document
            sentences = []
            for sent_start in sorted(sentences_tmp.keys()):
                sentences.append({"sent":sentences_tmp[sent_start],
                                  "id":f"{last_doc_id}."+"{:03d}".format(sent_start)})
            docs[last_doc_id] = sentences
            sentences_tmp = {}

            #handle nodes for this doc
            tree, stats = make_doc_node_list(nodes_tmp, possible_parents_tmp)
            trees[last_doc_id] = tree
            nodes_tmp = {}
            possible_parents_tmp = {}
            missing_parents_count += stats["missing_parents_count"]
            found_parents_count += stats["found_parents_count"]

        last_doc_id = doc_id
        sentence1 = datum["unit1_sent"]
        sentence2 = datum["unit2_sent"]
        sent1_start_str = datum["s1_toks"].split("-")[0]
        sent2_start_str = datum["s2_toks"].split("-")[0]
        node, parent_node = make_dep_node(datum)
        nodes_tmp[node["id"]] = node
        possible_parents_tmp[parent_node["id"]] = parent_node

        # print(f"doc_id: {doc_id}, sent1_pos: {sent1_start_str}, sent2_pos: {sent2_start_str}")

        try:
            sentence1_start = int(sent1_start_str)
            sentence2_start = int(sent2_start_str)

            for sent_start, sentence  in [(sentence1_start, sentence1), (sentence2_start, sentence2)]:
                if not sent_start in sentences_tmp.keys():
                    sentences_tmp[sent_start] = sentence
        except Exception as e:
            print(f"Problem with datum: {datum}")


    #store last doc
    if last_doc_id:
        sentences = []
        for sent_start in sorted(sentences_tmp.keys()):
            sentences.append({"sent": sentences_tmp[sent_start],
                              "id": f"{last_doc_id}." + "{:03d}".format(sent_start)})
        docs[last_doc_id] = sentences

        # handle nodes for this LAST doc
        tree, stats = make_doc_node_list(nodes_tmp, possible_parents_tmp)
        trees[last_doc_id] = tree
        missing_parents_count += stats["missing_parents_count"]
        found_parents_count += stats["found_parents_count"]

    print(f"Total missing parents: {missing_parents_count},  {missing_parents_count/len(data)*100}%")
    print(f"Total found parents: {found_parents_count},{found_parents_count/missing_parents_count*100}%")
    lost_count = missing_parents_count - found_parents_count
    print(f"Total lost parents: {lost_count},{lost_count/missing_parents_count*100}%")
    print(f"Total relations: {len(data)}")
    return data, docs, trees

def read_disrpt_connllu_for_raw_text(filename):
    docs = {} #key=doc_id, value= [ {"sent":<str>, "id":<str>} ... ]
    with open(filename, "r") as file:
        lines = file.readlines()
        sent_id = None
        doc_id = None
        text = None
        doc_sentences = []

        newdoc_prefix = "# newdoc_id = "
        sentid_prefix = "# sent_id = "
        text_prefix = "# text = "
        for i,line in enumerate(lines):
            if line.startswith(sentid_prefix):
                if lines[i+1].startswith(newdoc_prefix):
                    #save old doc
                    if len(doc_sentences)>0:
                        docs[doc_id] = doc_sentences

                    #start new doc
                    doc_sentences = []
                    doc_id = lines[i+1][len(newdoc_prefix)-1:].strip()
                sent_id = line[len(sentid_prefix)-1:].strip()
            elif line.startswith(text_prefix):
                text = line[len(text_prefix)-1:].strip()
                doc_sentences.append({
                    "sent":text,
                    "id":sent_id
                })

                #reset sentence info
                text = None
                sent_id = None

        ##save old doc
        docs[doc_id] = doc_sentences

    return docs

def get_first_word(string):
    first_word = string.split(" ")[0]  # take first word
    return  first_word

def get_tail(string):
    return " ".join(string.split(" ")[1:])  # remove first word

def convert(relation,  relations, raw_texts,
            context_mode=None, context_size=1, label_level=0):

    id = relation["doc"]+"."+relation["unit1_toks"]+"."+relation["unit2_toks"]

    arg1 = relation["unit1_txt"]
    arg2 = relation["unit2_txt"]
    # if relation["dir"] == "1>2":
    #     arg1 = relation["unit2_txt"]
    #     arg2 = relation["unit1_txt"]
    # print(id)

    #initialise final record
    result = {
        "id":id,
        "relation_class": None,
        "arg1": arg1,
        "arg1_org": arg1,
        "arg2": arg2,
        "conn": get_first_word(arg2),
        "arg2_org": arg2,
        "relation_type": "Implicit",
        "context": None,
        "truncation_length": None,
        "arg1_org_len": len(arg1),
        "context_mode": context_mode,
        "context_size": context_size,
        "context_provenance": None,
        "doc": relation["doc"]
    }
    corrected_label = relation["label"]
    if corrected_label:
        if "-" in corrected_label:
            corrected_label = corrected_label.split("-")[label_level]
        result["relation_class"] = corrected_label
    else:
        result["relation_class"] = "elab"  #hack
        print(f"WARNING: setting rel_class to dummy ELAB: data: {result}")

    if context_mode==3:
        #mode3: always add preceding sentence.
        doc_id = id.split(".")[0]
        sentences = raw_texts[doc_id]
        arg1_sentence = relation["unit1_sent"]
        matched_sentence = None
        cursor = -1
        for i, sentence in enumerate(sentences):
            target_sentence = sentence["sent"]
            cursor = i
            if arg1_sentence.strip()==target_sentence.strip():
                matched_sentence =target_sentence
                break   #assume 1 match only
        if not matched_sentence:
            print(f"Didn't find match for {doc_id} {arg1_sentence}")

        else:
            context = ""
            max_context = context_size
            if cursor - max_context < 0:
                max_context = cursor    # so the first offset will end up being the array start, or 0
            if cursor>0 and cursor<len(sentences):
                context_array = sentences[cursor - max_context:cursor]
                context_sentences = []
                for element in context_array:
                    context_sentences.append(element["sent"])
                context = " ".join(context_sentences)
            result["arg1"] = context + " ... " + arg1
            result["context"] = context
            provenance = sentences
            result["context_provenance"] = provenance


    return result

if __name__ == "__main__":
    print(f"Running converter of DISRPT rel files to ConnRel json files")
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_dir", required=True, help="DISRPT dir for component data set")
    args = parser.parse_args()
    filename = "eng.dep.covdtb_dev.rels"
    result = read_disrpt_rels(os.path.join(args.dataset_dir, filename))

    filename = "eng.dep.covdtb_dev.conllu"
    result = read_disrpt_connllu_for_raw_text(os.path.join(args.dataset_dir, filename))

    print (f"raw file: {len(result.keys())}")