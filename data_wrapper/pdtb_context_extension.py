import os, json

from data_wrapper.context_manager_pdtb_default import ContextManagerPDTB2
from data_wrapper.span_unentangler import SpanUnentangler
from data_wrapper.pdtb_data_wrapper import *
from data_wrapper.context_manager_joen import ContextManagerJoen

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

def is_same_datapoint(point1, point2, strip_rel_labels = True):
    # check args and type
    sample_arg1 = point1["arg1"]
    sample_arg2 = point1["arg2"]
    sample_relation_type = point1["relation_type"]

    contextual_arg1 = point2[R_ARG1]["arg_text"]
    contextual_arg2 = point2[R_ARG2]["arg_text"]
    contextual_relation_type = ""
    if strip_rel_labels:
        contextual_relation_type = point2["type"][4:-4]  # strip off the "____" before and after in e.g.,"____EntRel____"
    else:
        contextual_relation_type = point2["type"]  # for PDTB3, labels should be same.

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

mode_use_offsets = 0
mode_use_annotations = 1
mode_use_joen = 2
mode_use_joen_1baseline = 3

def read_pdtb_sample(cur_samples, input_filename, raw_text_location, dataset="pdtb2", mode=0, context_size=0,
                     jeon_segment_reader=None,
                     FLAG_preprocessing_version=2,
                     FLAG_emphasise_connectives=False
                    ):
    """
    This method intercepts the "cur_samples" data structure and adds extra context information to the samples.

    input_filename: if PDTB2, this has the file extension ".pdtb", if PDTB3, just the stub
    raw_text_location: if PDTB2, this is a directory where all the raw data is kept; if PDTB3, this the exact file

    Modes:
    0: use the raw context where offsets use to find all preceding text leading up to ARG1
    1: use annotations (dependent on context size)
    2: use automatic segmentation from Sungho Joen (dependent on context size)
    3: use Stanford segmentation to pick last sentence

    context_size: 1-99: use the *last* (most recent) n (n=mode#) immediate context, where a relationship was annotated.

    FLAG_prepocessing_version added 20121218.  Prior notes refer to preprocesing version >=2, so 2 is the default.

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
    annotations = None
    if dataset=="pdtb2":
        annotations = pdtb2_file_reader(input_filename)
    elif dataset=="pdtb3":
        annotations = pdtb3_file_reader(raw_text_location, input_filename)


    #STEP 1a. Integrate results with the original dicts.
    # pass information extracted from Wei Liu's data reader to this data reader (union, without clobbering)
    result = []
    for i,sample in enumerate(cur_samples):

        if is_same_datapoint(sample, annotations[i]):
            for key in sample.keys():
                if not key in annotations[i].keys():
                    annotations[i][key] = sample[key]

    # STEP 2. Analyse the filename to extract the (i) section and (2) filestub
    filename = os.path.basename(input_filename)
    section_dir = os.path.dirname(input_filename)
    section_string = os.path.basename(section_dir)
    raw_text_filepath = None

    doc_id = None
    file_stub = None
    if dataset== "pdtb2":
        #Need to figure out location of exact filename for this PDTB2 annotation file
        file_stub = filename[:-len(".pdtb")]  #strip off the ".pdtb" extension

        filenum = file_stub.split("_")[1]  # e.g., 0001
        doc_id = filenum

        print(f"filename: {filename}, section_str: {section_string}, file_stub:{file_stub}")

        raw_text_dir = raw_text_location
        raw_text_section_dir = os.path.join(raw_text_dir, section_string)
        raw_text_filepath = os.path.join(raw_text_section_dir, file_stub)

    elif dataset=="pdtb3":
        raw_text_filepath = raw_text_location
        raw_filename = os.path.basename(raw_text_filepath)   #eg. wsj_0002 -> 0002
        doc_id = raw_filename.split("_")[1]
        file_stub = raw_filename

    # STEP 3. Call the file reader for the raw data with information in step 2.
    raw_contents = read_raw(raw_text_filepath)

    #STEP 4. Extract context
    FLAG_consider_all = False
    stats = None
    if mode in [mode_use_offsets, mode_use_annotations]:
        context_manager = ContextManagerPDTB2()
        annotations, stats = context_manager.add_context(doc_id=doc_id, annotations=annotations, raw_text=raw_contents,
                                                  consider_all=FLAG_consider_all,
                                                  emphasise_connectives=FLAG_emphasise_connectives,
                                                  context_mode=mode)
    elif mode == mode_use_joen or mode == mode_use_joen_1baseline:
        context_manager = ContextManagerJoen(jeon_segment_reader)
        annotations, _ = context_manager.add_context(doc_id=doc_id, annotations=annotations, raw_text=raw_contents,
                                                  consider_all=FLAG_consider_all,
                                                  emphasise_connectives=FLAG_emphasise_connectives,
                                                  context_mode=mode)

    #STEP 5. integrate results with the original dicts.
    result = []
    context_len_dist = {}

    ex_connective_start_delimiter = ""
    ex_connective_end_delimiter = ""
    im_connective_start_delimiter = " "             #default: a space to separate inserted connective
    im_connective_end_delimiter = " "               #default: a space to separate inserted connective

    if FLAG_emphasise_connectives:
        ex_connective_start_delimiter = " # "
        ex_connective_end_delimiter = " @ "
        im_connective_start_delimiter = " ## "
        im_connective_end_delimiter = " @@ "

    for i,sample in enumerate(cur_samples):

        if is_same_datapoint(sample, annotations[i]):

            #Add extra provenance data
            # sample['id'] = f"{section_string}.{file_stub}.{i:03d}"
            sample['id'] = f"{section_string}.{doc_id}.{i:03d}"
            sample['section'] = section_string
            sample['filestub'] = file_stub
            sample['arg1_org'] = sample['arg1']
            #Add context

            some_context = ""
            processed_chained_context = []
            new_arg1_string = sample["arg1"]  #default no change
            #Mode 0: Context== all preceding leading up to ARG1
            if mode==0:
                some_context = annotations[i]["context"]["raw"]
                new_arg1_string = some_context + " " + sample["arg1"]           #creating the new string depends on mode


            #MODE 1: Context== most recent n (n=mode#) relationship where this sent/arg was an ARG2
            elif mode==1:
                if context_size > 0: #Need to the prune context as needed
                    #1 < context_size < 99: means amount of gold relationships to use
                    chained_context = annotations[i]["context"]["chained"]
                    chained_context_offsets = annotations[i]["context"]["chained_offsets"]
                    # print(f"SUMMARY: chained_length consider_all={FLAG_consider_all}: {len(chained_context)}")
                    if len(chained_context) > 0:
                        # print(f"\n {chained_context}  & {sample['arg1']} # {sample['conn']} @ {sample['arg2']}\n")
                        # print(f"\n {chained_context_offsets}")

                        # print(f"-------------------------------------------")
                        # print(f"chained_context: {chained_context}, chained_context_offsets: {chained_context_offsets}")

                        unentangler = SpanUnentangler()
                        kept_spans, boundary = unentangler.make_non_overlapping_context_chain(chained_context, chained_context_offsets)

                        # print(f"kept_spans: {kept_spans}, boundary: {boundary}")


                        processed_chained_context = []
                        for key in sorted(kept_spans.keys()):
                            processed_chained_context.append(kept_spans[key]["text"])

                        processed_chained_context_offsets = []  #has same length as processed_chained_context
                        for key in sorted(kept_spans.keys()):
                            processed_chained_context_offsets.append(
                                (kept_spans[key]["start"], kept_spans[key]["end"])
                            )

                        #clobber original chained_context
                        chained_context = processed_chained_context

                        offset = context_size
                        if offset > len(chained_context):
                            offset = len(chained_context)

                        some_context_list = chained_context[-offset:]  #context_size is number of context sentences to use
                        some_context_list_offsets = processed_chained_context_offsets[-offset:]  #context_size is number of context sentences to use
                        some_context_connective_list = annotations[i]["context"]["chained_connectives"][-offset:]

                        #store offset dist
                        if not offset in context_len_dist.keys():
                            context_len_dist[offset] = 1
                        else:
                            context_len_dist[offset] += 1

                        annotations[i]["context"]["context_full_processed_chain"] = processed_chained_context  # store it for later

                        #now add the context
                        some_context = ". ".join(some_context_list)
                        new_arg1_string = some_context + " " + sample["arg1"]           #creating the new string depends on mode

                        if FLAG_preprocessing_version==3:
                            context_and_args = [x for x in some_context_list]
                            context_and_args.append(sample["arg1"])
                            context_and_args_offsets = [x for x in some_context_list_offsets]
                            context_and_args_offsets.append(annotations[i][R_ARG1]["arg_span_list"][0])  #take 1st offset in arg1 span_list

                            merged_context_arg1, merged_boundary = \
                                unentangler.make_non_overlapping_context_chain(context_and_args, context_and_args_offsets)

                            # print(
                            #     f"context_and_args: {context_and_args}, context_and_args_offsets: {context_and_args_offsets}")
                            # print(f"merged_context_arg1: {merged_context_arg1}, boundary: {merged_boundary}")

                            merged_context_arg1_texts = []
                            last_seen_offset = None
                            for key in sorted(merged_context_arg1.keys()):
                                # print(f"last_seen_offset: {last_seen_offset}")
                                component_start = merged_context_arg1[key]["start"]
                                component_end = merged_context_arg1[key]["end"]
                                component_offsets = (component_start, component_end)
                                component_text = merged_context_arg1[key]["text"]

                                padding = ""
                                if last_seen_offset:
                                #     diff = component_start - last_seen_offset
                                #
                                #     print(f"diff: {diff}, component_start: {component_start}")
                                #
                                #     padding = "".ljust(diff, " ")     #need to -1 as slices are right-exclusive

                                    padding = raw_contents[last_seen_offset+1:component_start]
                                    # print(f"padding: {last_seen_offset+1}-{component_start}//{padding}//")

                                last_seen_offset = component_end
                                merged_context_arg1_texts.append(f"{padding}{component_text}")

                            # print(f"merged_context_arg1_texts: {merged_context_arg1_texts}")

                            merged_arg1_string = "".join(merged_context_arg1_texts)

                            # print(f"merged_arg1_string: {merged_arg1_string}")

                            # now add in the connectives
                            new_merged_string = ""
                            last_connective_offset = 0
                            for connective_edit in some_context_connective_list:

                                connective_start_pos = connective_edit["start"] - merged_boundary[0]
                                new_merged_string += merged_arg1_string[last_connective_offset:connective_start_pos]
                                last_connective_offset = connective_start_pos

                                # print(f"connective: {connective_edit}")

                                if connective_edit["type"]  == "____Explicit____":

                                    #by definition (of explicit) the connective span has to overlap with this
                                    connective_end_pos = connective_edit["end"] - merged_boundary[0]
                                    connective = merged_arg1_string[connective_start_pos:connective_end_pos]

                                    new_merged_string += f"{ex_connective_start_delimiter}{connective}{ex_connective_end_delimiter}"
                                    last_connective_offset = connective_end_pos


                                elif connective_edit["type"] == "____Implicit____":
                                    connective = connective_edit["text"]
                                    new_merged_string += f"{im_connective_start_delimiter}{connective}{im_connective_end_delimiter}"

                            new_merged_string += merged_arg1_string[last_connective_offset:]  #consume remainder of the string
                            new_arg1_string = new_merged_string


                            # print(f"new arg1: {new_arg1_string}")
                            # print(f"-------------------------------------------")

                # print(f"SUMMARY: Context len dist: {context_len_dist}")  # print to stdout distribution of context offset lengths for this preprocessing job

            elif mode==2 or mode==3:
                #use Jeon segmentations
                offset = context_size
                chained_context = annotations[i]["context"]["chained"]
                if offset > len(chained_context):
                    offset = len(chained_context)

                some_context_list = chained_context[-offset:]  # context_size is number of context sentences to use
                some_context = ". ".join(some_context_list)
                new_arg1_string = some_context + " " + sample["arg1"]           #creating the new string depends on mode

            #add context info to sample (no matter which mode)
            sample["context_provenance"] = annotations[i]["context"]

            #Apply truncation regardless of context mode type
            sample["context"] = some_context
            # new_string = some_context + " " + sample["arg1"]
            sample['arg1'], sample['truncation_length'], sample['arg1_org_len'] = truncate(new_arg1_string)
            sample["context_mode"] = mode
            sample["context_size"] = context_size

            # #trace writes to debug
            if context_size > 0:
                #have to use Wei Liu's relation strings (so no ___ before and after the type label
                if len(sample["context_provenance"]["chained"]) > 0  and sample["relation_type"]=="Implicit":
                    print(f"-----------\n {json.dumps(sample, indent=3)} \n -----------------")

            #finalise result
            result.append(sample)

    return result, stats

