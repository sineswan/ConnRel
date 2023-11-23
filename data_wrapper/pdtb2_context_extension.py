import os, json

from data_wrapper.span_unentangler import SpanUnentangler

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


def read_raw(filename):
    text = None
    with open(filename, encoding="latin-1") as file:  # PDTB2 encoded as ascii (not utf-8)
        text = file.read()
    return text

def add_context(annotations, raw_text, consider_all=False):

    #assuming annotations are in order
    arg1s = {}
    arg2s = {}

    dependencies = {}
    dependency_offsets = {}

    mode1_stats = {
        "found":0,
        "not_found":0,
        R_ENTREL:0,
        R_IMPLICIT:0,
        R_EXPLICIT:0,
        R_NOREL:0,
        R_ALTLEX:0
    }

    for i,annotation in enumerate(annotations):
        annotation["context"] = None

        #save args to internal dicts
        arg1 = annotation[R_ARG1]["arg_text"]
        arg2 = annotation[R_ARG2]["arg_text"]
        # Find the earliest point to trackback to find context
        arg1_start = annotation[R_ARG1]["arg_span_list"][0][0] #1st element, 1st offset
        arg2_start = annotation[R_ARG2]["arg_span_list"][0][0]  # 1st element, 1st offset
        if not arg1 in arg1s.keys():
            arg1s[arg1] = [i]
        else:
            arg1s[arg1].append(i)

        if not arg2 in arg2s.keys():
            arg2s[arg2] = [i]
        else:
            arg2s[arg2].append(i)

        annotation["context"] = {}
        #Mode 0
        if raw_text:   #so assuming there's original content to get context

            context = ""
            # print(f"Arg start chars: {arg1_start} {arg2_start}")
            arg_start_min = min(arg1_start, arg2_start)
            # print(f"min: {arg_start_min}")
            context = raw_text[:arg_start_min]

            # print(f"Arg start chars: {arg1_start} {arg2_start}: {context}")
            annotation["context"]["raw"] = context

        #Mode 1-99: use gold context
        if True: #mode < 100:

            found_match = None
            for an_arg2 in arg2s.keys():
                if arg1 in an_arg2 or an_arg2 in arg1:  #some nested substring exists:
                    found_match = an_arg2

            if found_match:
                # print(f"FOUND prior dependency: ARG1: {arg1}, found_match: {found_match}, ARG2: {arg2} ")
                mode1_stats["found"] += 1

                #We loop over all data points with this prior arg2 which might break linear order of text but this is rare.
                dep_context = []
                dep_context_offsets = []
                for dep_id in arg2s[found_match]:

                    prior_dep = annotations[dep_id]

                    # print(f"prior_dep: \n {json.dumps(prior_dep, indent=3)}")

                    prior_arg = prior_dep[R_ARG1]["arg_text"]
                    prior_connective = prior_dep["conn"]
                    prior_discourse_type = prior_dep["type"]
                    candidate_prior_arg = prior_arg

                    # position tuple is in a list (usually singleton); take 1st
                    prior_arg_start = prior_dep[R_ARG1]["arg_span_list"][0][0]
                    # position tuple is in a list (usually singleton); take 2nd
                    prior_arg_end = prior_dep[R_ARG1]["arg_span_list"][0][1]
                    earliest_char_pos = prior_arg_start
                    latest_char_pos = prior_arg_end

                    if prior_discourse_type in annot_has_relationship:
                        #find the prior_arg and conn offsets and find the outer set (maximal string)

                        prior_connective_positions = None
                        if prior_discourse_type == R_IMPLICIT:
                            # it's a nominal char position where the connective would be inserted.
                            prior_connective_position = prior_dep["string_pos"]
                            if prior_connective_position < prior_arg_start :
                                candidate_prior_arg = " # "+prior_connective+" @ "+candidate_prior_arg
                            else:
                                candidate_prior_arg = candidate_prior_arg + " # " + prior_connective + " @ "
                        else:
                            #could be a range
                            prior_connective_position = prior_dep["main_span_list"]
                            prior_connective_positions = prior_connective_position[0]

                            #prior_connective_positions are now set

                            #Connective could come before arg1: e.g., Although ARG1 ... ARG2
                            earliest_char_pos = (prior_arg_start) if \
                                (prior_arg_start < prior_connective_positions[0]) else prior_connective_positions[0]

                            #always use prior_arg_end because if the connective comes after it is the start of a new sent
                            candidate_prior_arg = raw_text[earliest_char_pos:prior_arg_end]
                            # if prior_connective_position[1] > prior_arg_end:

                            candidate_prior_arg += " #_ "+prior_connective+" _@ "

                    mode1_stats[prior_discourse_type] += 1

                    #find preceding (accumulated) dependencies
                    if prior_arg in dependencies.keys():
                        #need to iterate to *copy* content (i.e., duplicate) to new dep_context for THIS data point
                        for deps in dependencies[prior_arg]:
                            dep_context.append(deps)
                        for deps_start, deps_end in dependency_offsets[prior_arg]:
                            dep_context_offsets.append((deps_start, deps_end))  #duplicate tuple

                    #Only use (explicit or implicitly marked) discourse relationships
                    if (consider_all and prior_discourse_type in annot_exists) or \
                        (prior_discourse_type in annot_has_relationship):
                            # print(f"prior connective: {prior_connective}")
                            dep_context.append(candidate_prior_arg)
                            dep_context_offsets.append((earliest_char_pos, latest_char_pos))

                # print(f"len(chained_context): {len(dep_context)}: {dep_context}\n")
                annotation["context"]["chained"] = dep_context
                annotation["context"]["chained_offsets"] = dep_context_offsets
                annotation["context"]["chained_source_ids"] = arg2s[found_match]

                #accumulate dependencies for this matched arg1
                dependencies[arg1] = dep_context
                dependency_offsets[arg1] = dep_context_offsets

            else:
                # print(f"NOT FOUND prior dependency: ARG1: {arg1}, dependencies: {None}")
                annotation["context"]["chained"] = []
                annotation["context"]["chained_offsets"] = []
                annotation["context"]["chained_source_ids"] = []
                mode1_stats["not_found"] += 1

    print(f"SUMMARY mode1_stats: {mode1_stats}")
    return annotations

from transformers import AutoTokenizer

# checkpoint = "bert-base-uncased"
checkpoint = "roberta-base"  #similar to RoBERTa
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
def truncate(text, max_length=512):
    truncated_text = text
    transformer_tokenisation = tokenizer(truncated_text)
    length = len(transformer_tokenisation["input_ids"])
    org_length = length
    while length > max_length:
        first_space = text.find(" ")   #crucially, finds left-most (first) space.  Truncation happens from earliest point.
        if first_space == -1:
            #can't segment on word boundaries any more.
            break
        else:
            truncated_text = truncated_text[first_space+1:]   #+1 because we want the next char after the space.

            #calculate
            transformer_tokenisation = tokenizer(truncated_text)
            length = len(transformer_tokenisation["input_ids"])

    #check to see if length still needs fixing
    if length > max_length:
        print(f"Max length exceeded: {length}, text: {truncated_text}")
        raise Exception()

    if not text == truncated_text:
        print(f"Truncated text: success: {length} from {org_length}")

    truncation_length = org_length - length

    return truncated_text, truncation_length, org_length

def is_same_datapoint(point1, point2):
    # check args and type
    sample_arg1 = point1["arg1"]
    sample_arg2 = point1["arg2"]
    sample_relation_type = point1["relation_type"]

    contextual_arg1 = point2[R_ARG1]["arg_text"]
    contextual_arg2 = point2[R_ARG2]["arg_text"]
    contextual_relation_type = point2["type"][4:-4]  # strip off the "___" before and after in e.g.,"____EntRel____"

    FLAG_checkgood = True
    if not sample_arg1 == contextual_arg1 or \
            not sample_arg2 == contextual_arg2 or \
            not sample_relation_type == contextual_relation_type:
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

    return FLAG_checkgood

def read_pdtb2_sample(cur_samples, input_filename, raw_text_dir, mode=0):
    """
    This method intercepts the "cur_samples" data structure and adds extra context information to the samples.

    Modes:
    0: use the raw context where offsets use to find all preceding text leading up to ARG1
    1-99: use the *last* (most recent) n (n=mode#) immediate context, where a relationship was annotated.
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


    #STEP 1a. Integrate results with the original dicts.
    # pass information extracted from Wei Liu's data reader to this data reader (union, without clobbering)
    result = []
    for i,sample in enumerate(cur_samples):

        if is_same_datapoint(sample, annotations[i]):
            for key in sample.keys():
                if not key in annotations[i].keys():
                    annotations[i][key] = sample[key]



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
    FLAG_consider_all = False
    annotations = add_context(annotations, raw_contents, consider_all=FLAG_consider_all)

    #STEP 5. integrate results with the original dicts.
    result = []
    context_len_dist = {}
    for i,sample in enumerate(cur_samples):

        if is_same_datapoint(sample, annotations[i]):

            #Add extra provenance data
            sample['id'] = f"{section_string}.{file_stub}.{i:03d}"
            sample['section'] = section_string
            sample['filestub'] = file_stub
            sample['arg1_org'] = sample['arg1']
            #Add context

            some_context = ""
            processed_chained_context = []
            #Mode 0: Context== all preceding leading up to ARG1
            if mode==0:
                some_context = annotations[i]["context"]["raw"]

            #MODE 1: Context== most recent n (n=mode#) relationship where this sent/arg was an ARG2
            else:
                if mode < 100:
                    #1 < mode < 99: means amount of gold relationships to use
                    some_context = ""
                    chained_context = annotations[i]["context"]["chained"]
                    chained_context_offsets = annotations[i]["context"]["chained_offsets"]
                    # print(f"SUMMARY: chained_length consider_all={FLAG_consider_all}: {len(chained_context)}")
                    if len(chained_context) > 0:
                        # print(f"\n {chained_context}  & {sample['arg1']} # {sample['conn']} @ {sample['arg2']}\n")
                        # print(f"\n {chained_context_offsets}")

                        unentangler = SpanUnentangler()
                        kept_spans = unentangler.make_non_overlapping_context_chain(chained_context, chained_context_offsets)

                        processed_chained_context = []
                        for key in sorted(kept_spans.keys()):
                            processed_chained_context.append(kept_spans[key]["text"])

                        #clobber original chained_context
                        chained_context = processed_chained_context

                        offset = mode
                        if offset > len(chained_context):
                            offset = len(chained_context)

                        some_context = chained_context[-offset:]  #mode is number of contect sentences to use

                        #store offset dist
                        if not offset in context_len_dist.keys():
                            context_len_dist[offset] = 1
                        else:
                            context_len_dist[offset] += 1

            #add context info to sample (no matter which mode)
            sample["context"] = ". ".join(some_context)
            sample["context_provenance"] = annotations[i]["context"]
            sample["context_full_procecssed_chain"] = processed_chained_context  # store it for later

            #Apply truncation regardless of context mode type
            new_string = sample["context"] + " " + sample["arg1"]
            sample['arg1'], sample['truncation_length'], sample['arg1_org_len'] = truncate(new_string)
            sample["context_mode"] = mode

            #trace writes to debug
            if mode > 0:
                #have to use Wei Liu's relation strings (so no ___ before and after the type label
                if len(sample["context_full_procecssed_chain"]) > 0  and sample["relation_type"]=="Implicit":
                    print(f"-----------\n {json.dumps(sample, indent=3)} \n -----------------")

            #finalise result
            result.append(sample)

    print(f"SUMMARY: Context len dist: {context_len_dist}")  #print to stdout distribution of context offset lengths for this preprocessing job
    return result

