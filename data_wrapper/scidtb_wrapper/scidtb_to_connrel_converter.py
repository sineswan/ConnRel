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


def convert(relation, context_index=None):
    id = relation["doc"]+"."+relation["unit1_toks"]+"."+relation["unit2_toks"]

    arg1 = relation["unit1_txt"]
    arg2 = relation["unit2_txt"]
    if relation["dir"] == "1>2":
        arg1 = relation["unit2_txt"]
        arg2 = relation["unit1_txt"]
    label = relation["label"]
    filename = relation["doc"]
    print(filename)

    #find context
    if context_index:
        context = None
        an_index = context_index[filename+".edu.txt.dep"]
        context = an_index[arg1]
        arg1 = context + " ... " + arg1


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


    result = {
        "relation_class": corrected_label,
        "arg1": arg1,
        "arg2": arg2,
        "conn": conn,
        "relation_type": "Implicit",
        "id":id
    }
    return result