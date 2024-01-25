from resources import scidtb_filtered_connectives as filtered_conns

def get_first_word(string):
    first_word = string.lower().split(" ")[0]  # take first word, make lowercase
    return  first_word

def get_tail(string):
    return " ".join(string.lower().split(" ")[1:])  # remove first word, make lowercase

def pick_conn(label):
    a_dict = filtered_conns[label]
    sorted_hist = {k: v for k, v in sorted(a_dict.items(), key=lambda item: item[1], reverse=True)}
    result = None
    for key in sorted_hist.keys():
        #should be sorted by freq/value, so take 1st key
        result = key
        break
    return result


def convert(relation, context_index=None,  context_mode=None, context_size=0, dataset_fileext=".edu.txt.dep"):
    """

    Args:
        relation:
        context_index: a dicts.  "context" key is an ordered array of context records for this relation
        context_mode:
        context_size:
        dataset_fileext:

    Returns:

    """
    id = relation["doc"]+"."+relation["unit1_toks"]+"."+relation["unit2_toks"]

    arg1 = relation["unit1_txt"]
    arg2 = relation["unit2_txt"]
    if relation["dir"] == "1>2":
        arg1 = relation["unit2_txt"]
        arg2 = relation["unit1_txt"]
    label = relation["label"]
    filename = relation["doc"]
    print(id)

    #initialise final record
    result = {
        "id":id,
        "relation_class": None,
        "arg1": arg1,
        "arg1_org": arg1,
        "arg2": arg2,
        "conn": None,
        "relation_type": "Implicit",
        "context": None,
        "truncation_length": None,
        "arg1_org_len": len(arg1),
        "context_mode": context_mode,
        "context_size": context_size,
        "context_provenance": None
    }

    #find context
    if context_mode:
        context_record = None
        provenance = None
        if context_index:
            context = None
            an_index = context_index[filename+dataset_fileext]
            context = ""
            if arg1 in an_index.keys():
                provenance = an_index[arg1]
                context_record = provenance["context"][0]
                if context_record:
                    context = context_record["text"]
            else:
                #have to use fuzzy matching
                for key in an_index.keys():
                    if arg1.startswith(key) or key.startswith(arg1):
                        provenance = an_index[key]
                        context_record = provenance["context"][0]
                        if context_record:
                            context = context_record["text"]
                        break
                if context == "": #still empty
                    print(f"WARNING: missing context for {id}, arg1: {arg1}")
            if not context: #context is a None
                context = ""
                print(f"WARNING: empty context for {id}, arg1: {arg1}")

            result["arg1"] = context + " ... " + arg1
            result["context"] = context
            result["context_provenance"] = provenance

    #determine connective
    conn = get_first_word(arg2)
    alt_arg2 = get_tail(arg2)
    if label in filtered_conns.keys():
        if conn in filtered_conns[label].keys():
            #this conn is in the vetted list, so use it, and pop it from arg2 (==alt_arg2)
            arg2 = alt_arg2
        else:
            #this conn is NOT in vetted list, pick another from the vetted list
            #keep arg2 as it is
            conn = pick_conn(label)
    else:
        print(f"WARNING: Missing label: {label}")
        conn = "and"

    corrected_label = relation["label"]
    if "-" in corrected_label:
        corrected_label = corrected_label.split("-")[0]


    result["relation_class"] = corrected_label
    result["conn"] = conn

    return result