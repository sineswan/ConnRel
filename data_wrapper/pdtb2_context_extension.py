import os

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
    """ Rewritten version of Wei Liu's oode to extract more contextual information """

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


def read_raw(filename):
    text = None
    with open(filename, encoding="latin-1") as file:  # PDTB2 encoded as ascii (not utf-8)
        text = file.read()
    return text

def add_context(annotations, raw_text):

    for annotation in annotations:
        annotation["context"] = None

        if raw_text:   #so assuming there's original content to get context

            # Find the earliest point to trackback to find context
            arg1_start = annotation[R_ARG1]["arg_span_list"][0][0] #1st element, 1st offset
            arg2_start = annotation[R_ARG2]["arg_span_list"][0][0]  # 1st element, 1st offset

            # print(f"Arg start chars: {arg1_start} {arg2_start}")
            arg_start_min = min(arg1_start, arg2_start)
            # print(f"min: {arg_start_min}")
            context = raw_text[:arg_start_min]

            # print(f"Arg start chars: {arg1_start} {arg2_start}: {context}")
            annotation["context"] = {"raw":context}

    return annotations


from transformers import AutoTokenizer

# checkpoint = "bert-base-uncased"
checkpoint = "roberta-base"  #similar to RoBERTa
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
def truncate(text, max_length=512):
    transformer_tokenisation = tokenizer(text)
    length = len(transformer_tokenisation)
    print(f"max: {max_length}, this: {length}")
    if length > max_length:
        print(f"Max length exceeded: {length}")
        raise Exception()

    return text

def read_pdtb2_sample(cur_samples, input_filename, raw_text_dir):
    """
    This method intercepts the "cur_samples" data structure and adds extra context information to the samples.
    """

    # This method relies on the original data reading code of ConnRel (ACL 2023)
    # It calls a duplicate method to read the PDTB label files to extract offsets (missing in the original code)
    #   and the PDTB raw data to extract the context (with aforementioned offsets.
    #
    # To do this, we:
    #    1. Call alternative PDTB2 label file reader
    #    2. Analyse the filename to extract the (i) section and (2) filestub
    #    3. Call the file reader for the raw data with information in step 2.
    #    4. Extract context
    #    5. integrate results with the original dicts.

    #STEP 1. Call alternative PDTB2 label file reader
    annotations = pdtb2_file_reader(input_filename)

    #STEP 2. Analyse the filename to extract the (i) section and (2) filestub
    filename = os.path.basename(input_filename)
    section_dir = os.path.dirname(input_filename)
    section_string = os.path.basename(section_dir)
    file_stub = filename[:-len(".pdtb")]  #strip off the ".pdtb" extension

    print(f"filename: {filename}, section_str: {section_string}, file_stub:{file_stub}")

    raw_text_section_dir = os.path.join(raw_text_dir, section_string)
    raw_text_filepath = os.path.join(raw_text_section_dir, file_stub)

    #STEP 3. Call the file reader for the raw data with information in step 2.
    raw_contents = read_raw(raw_text_filepath)

    #STEP 4. Extract context
    annotations = add_context(annotations, raw_contents)

    #STEP 5. integrate results with the original dicts.
    result = []
    for i,sample in enumerate(cur_samples):

        #check args and type
        sample_arg1 = sample["arg1"]
        sample_arg2 = sample["arg2"]
        sample_relation_type = sample["relation_type"]

        contextual_arg1 = annotations[i][R_ARG1]["arg_text"]
        contextual_arg2 = annotations[i][R_ARG2]["arg_text"]
        contextual_relation_type = annotations[i]["type"][4:-4]  #strip off the "___" before and after in e.g.,"____EntRel____"

        FLAG_checkgood = True
        if not sample_arg1==contextual_arg1 or \
            not sample_arg2==contextual_arg2 or \
            not sample_relation_type==contextual_relation_type:
            FLAG_checkgood = False

        if not FLAG_checkgood:
            error_string = "Error with: "
            if not sample_arg1 == contextual_arg1:
                print(f"sample_arg1:\n --{sample_arg1}--")
                print(f"contextual_arg1:\n --{contextual_arg1}--")
                error_string += " ARG1"
            if not sample_arg2 == contextual_arg2:
                print(f"sample_arg2:\n --{sample_arg2}--")
                print(f"contextual_arg2:\n --{contextual_arg2}--")
                error_string += " ARG2"
            if not sample_relation_type == contextual_relation_type:
                print(f"sample_rel:\n --{sample_relation_type}--")
                print(f"contextual_rel:\n --{contextual_relation_type}--")
                error_string += " REL"


            print(f"NOT MATCHING: {error_string}")
            raise Exception("Data points not aligned: "+error_string)
        else:

            #Add extra provenance data
            sample['id'] = f"{section_string}.{file_stub}.{i:03d}"
            sample['section'] = section_string
            sample['filestub'] = file_stub
            sample['arg1_org'] = sample['arg1']
            #Add context
            sample["context"] = annotations[i]["context"]["raw"]
            sample['arg1'] = truncate(sample["context"]+" "+sample["arg1"])

            result.append(sample)

    return result

