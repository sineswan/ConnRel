import regex as re

#referencing the fileformat.pdf documentation for PDTB2 outlining BDF rules for the annotation
R_ARG1 = "____Arg1____"
R_ARG2 = "____Arg2____"
R_EXPLICIT = "____Explicit____"
R_IMPLICIT = "____Implicit____"
R_ENTREL = "____EntRel____"
R_ALTLEX = "____AltLex____"
R_NOREL =  "____NoRel____"

data_splits = { #
    "test":["21","22"],
    "dev":["00", "01"]
}

annot_relation_strings = [R_EXPLICIT, R_IMPLICIT]
annot_other_strings = [R_ENTREL, R_ALTLEX, R_NOREL]
annot_arg_strings = [R_ARG1, R_ARG2]
annot_has_selection_string = [R_EXPLICIT, R_ALTLEX]  #others have "inferenceSite
annot_has_relationship = [R_EXPLICIT, R_IMPLICIT, R_ALTLEX]  #has a relationship but ALTLEX has no connective
annot_exists = [R_EXPLICIT, R_IMPLICIT, R_ALTLEX, R_ENTREL]  #anything but NOREL

#header_row_mapping always assumes 1st element (idx=0) is the subsection type: rel_type, arg1, arg2
#these are array indices, for an array of strings
selection_header_row_mapping = {
    "span_list":1,
    "gorn":2,
    "text":4,
    "features":7,
    "rel_info":-1}
inference_site_header_row_mapping = {
    "string_pos":1,
    "sent_num":2,
    "features":4,
    "rel_info":5}
arg_header_row_mapping = {
    "span_list":1,
    "gorn":2,
    "text":4,
}



def get_span_list(line):
    span_list = line.strip().split(";")
    result = []
    for span in span_list:
        a_span = span.split("..")
        new_span = [int(x) for x in a_span]
        result.append(new_span)
    return result

def get_relation(line):
    parts = line.strip().split(",")
    result = {
        "connective":parts[0]
    }
    if len(parts)>1:
        result["class"] = parts[1]
    return result

def get_arg(sample_lines, arg_name):

    # SpanList
    result = {"type":arg_name}
    span_list_line = sample_lines[arg_header_row_mapping["span_list"]]
    result["arg_span_list"] = get_span_list(span_list_line)

    # text_line = sample_lines[arg_header_row_mapping["text"]]
    # result["arg_text"] = text_line.strip()

    arg_text_list = [ sample_lines[arg_header_row_mapping["text"]] ]
    # Check for extra lines  (behaviour forced to be consistent wit Wie Liu's though minor bug detected 20231012
    pointer = arg_header_row_mapping["text"] + 1
    while pointer < len(sample_lines) -1:
        line = sample_lines[pointer]

        if not line.startswith("##############"):
            arg_text_list.append(line)
        else:
            break

        pointer += 1

    arg_text = ", ".join([t.replace("\n","") for t in arg_text_list])   #comma separator is not right, making same as Wei Liu's
    result["arg_text"] = arg_text

    return result

def pdtb2_sample_reader(sample_lines):
    """ Rewritten version of Wei Liu's code to extract more contextual information """

    block = {}    #will be a dict of fields for this row/datum

    #First break sample into pre, arg1, arg2 subblocks
    boundaries = [0] #0, arg1 line, arg2 line;   #value is the START of boundary

    #first line should be the type
    block["type"] = sample_lines[0].strip()

    #Find segmentations for PRE, ARG1, ARG2 subsections
    for i,line in enumerate(sample_lines):
        c_line = line.strip()
        if c_line in annot_arg_strings:
            boundaries.append(i)


    ########################################
    #process PRE
    ########################################
    pre_sample_lines = sample_lines[boundaries[0]:boundaries[1]]

    if block["type"] in annot_relation_strings:
        # Relation
        relation_line = pre_sample_lines[selection_header_row_mapping["rel_info"]]
        block["relation"] = get_relation(relation_line)

    if block["type"] in annot_has_selection_string:
        # OPTION 1. this is an Explicit or AltLex relation, look for a selection SpanList + GornList
        #SpanList
        span_list_line = pre_sample_lines[selection_header_row_mapping["span_list"]]
        block["main_span_list"] = get_span_list(span_list_line)
    else:
        #this annotation has an inference_site

        #String position
        string_pos_line = pre_sample_lines[inference_site_header_row_mapping["string_pos"]]
        block["string_pos"] = int(string_pos_line.strip())

        #Sentence Number
        sent_num_line = pre_sample_lines[inference_site_header_row_mapping["sent_num"]]
        block["sent_num"] = int(sent_num_line.strip())


    ########################################
    #process ARG1
    ########################################
    arg1_sample_lines = sample_lines[boundaries[1]:boundaries[2]]
    block[R_ARG1] = get_arg(arg1_sample_lines, R_ARG1)


    ########################################
    #process ARG2
    ########################################
    arg2_sample_lines = sample_lines[boundaries[2]:]
    block[R_ARG2] = get_arg(arg2_sample_lines, R_ARG2)

    return block

def pdtb2_file_reader(input_file):
    """Unchanged from Wei Liu's original"""
    all_samples = []
    with open(input_file, "r", encoding="ISO-8859-1") as f:
        lines = f.readlines()
        sample_boundaries = []
        for idx, line in enumerate(lines):
            line = line.strip()
            if "____Explicit____" in line or "____NoRel____" in line or "____EntRel____" in line \
                    or "____Implicit____" in line or "____AltLex____" in line:
                sample_boundaries.append(idx)

        sample_boundaries.append(idx) # add the last one
        boundary_size = len(sample_boundaries)
        for idx in range(boundary_size-1):
            sample_lines = lines[sample_boundaries[idx]:sample_boundaries[idx+1]]
            sample = pdtb2_sample_reader(sample_lines)
            all_samples.append(sample)
            # if sample["relation_type"] == "Implicit":
            #     all_samples.append(sample)

    return all_samples

def pdtb3_file_reader(data_file, label_file):
    """
    Based one original function by Wei Liu:
    https://github.com/liuwei1206/ConnRel/blob/907e7fa676fe58197f0638a2673c058f778227b6/preprocessing.py#L193

    Args:
        data_file: file path for raw text data
        label_file: label info for each data
    """
    all_samples = []

    with open(data_file, "r", encoding="latin1") as f: # utf-8
        text_data = f.read()

    with open(label_file, "r", encoding="latin1") as f: # utf-8
        lines = f.readlines()
        for line in lines:
            if line:
                items = line.split("|")

                relation_type = items[0].strip()
                conn1 = items[7].strip()
                conn1_sense1 = items[8].strip()
                conn2 = items[10].strip()
                conn2_sense1 = items[11].strip()

                arg1_idx = items[14].split(";")
                arg2_idx = items[20].split(";")
                arg1_str = []
                for pairs in arg1_idx:
                    arg1_i, arg1_j = pairs.split("..")
                    arg1 = text_data[int(arg1_i):int(arg1_j)+1]
                    arg1_str.append(re.sub("\n", " ", arg1))
                arg1 = ", ".join(arg1_str)

                arg2_str = []
                for pairs in arg2_idx:
                    if pairs == "":
                        continue
                    arg2_i, arg2_j = pairs.split("..")
                    arg2 = text_data[int(arg2_i):int(arg2_j)+1]
                    arg2_str.append(re.sub("\n", " ", arg2))
                arg2 = ", ".join(arg2_str)

                if int(arg1_idx[0].split("..")[0]) > int(arg2_idx[0].split("..")[0]):
                    tmp = arg1
                    arg1 = arg2
                    arg2 = tmp

                provenance = items[32].strip().lower()
                if "pdtb2" in provenance:
                    if "same" in provenance:
                        annotate_flag = "pdtb2.same"
                    elif "changed" in provenance:
                        annotate_flag = "pdtb2.changed"
                elif "pdtb3" in provenance:
                    annotate_flag = "pdtb3.new"

                sample = {}
                sample["relation_type"] = relation_type
                if conn1 and conn2:
                    sample["conn"] = conn1 + "##" + conn2
                elif conn1:
                    sample["conn"] = conn1
                elif conn2:
                    sample["conn"] = conn2
                else:
                    sample["conn"] = ""

                if conn1_sense1 and conn2_sense1:
                    sample["relation_class"] = conn1_sense1 + "##" + conn2_sense1
                elif conn1_sense1:
                    sample["relation_class"] = conn1_sense1
                elif conn2_sense1:
                    sample["relation_class"] = conn2_sense1
                else:
                    sample["relation_class"] = ""

                sample["arg1"] = arg1
                sample["arg2"] = arg2
                sample["annotate_flag"] = annotate_flag

                #--------------------------------------------
                # WAN (20231213): adding some extra attributes
                #--------------------------------------------

                #extra: dict structure for arg2
                sample["type"] = relation_type
                arg1_span_list = []
                for pairs in arg1_idx:
                    arg1_i, arg1_j = pairs.split("..")
                    arg1_span_list.append([int(arg1_i), int(arg1_j)])

                sample[R_ARG1] = {
                    "arg_text":arg1,
                    "arg_span_list":arg1_span_list
                }

                #extra: dict structure for arg2
                arg2_span_list = []
                for pairs in arg2_idx:
                    arg2_i, arg2_j = pairs.split("..")
                    arg2_span_list.append([int(arg2_i), int(arg2_j)])

                sample[R_ARG2] = {
                    "arg_text":arg2,
                    "arg_span_list":arg2_span_list
                }

                #extra: record connective offset(s)
                connective_location = items[-3]
                if relation_type in annot_has_selection_string:
                    # OPTION 1. this is an Explicit or AltLex relation, look for a selection SpanList + GornList
                    # SpanList
                    sample["main_span_list"] = get_span_list(connective_location)
                else:
                    # this annotation has an inference_site

                    # String position
                    sample["string_pos"] = int(connective_location.strip())

                all_samples.append(sample)

    return all_samples

def read_raw(filename):
    text = None
    with open(filename, encoding="latin-1") as file:  # PDTB2 encoded as ascii (not utf-8)
        text = file.read()
    return text

