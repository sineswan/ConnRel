import os, json

from data_wrapper.context_manager_pdtb2_default import ContextManagerPDTB2
from data_wrapper.span_unentangler import SpanUnentangler
from data_wrapper.pdtb2_data_wrapper import *


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

mode_use_offsets = 0
mode_use_annotations = 1
mode_use_joen = 2
def read_pdtb2_sample(cur_samples, input_filename, raw_text_dir, mode=0, context_size=0):
    """
    This method intercepts the "cur_samples" data structure and adds extra context information to the samples.

    Modes:
    0: use the raw context where offsets use to find all preceding text leading up to ARG1
    1: use annotations (dependent on context size)
    2: use automatic segmentation from Sungho Joen (dependent on context size)

    context_size: 1-99: use the *last* (most recent) n (n=mode#) immediate context, where a relationship was annotated.
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
    if mode in [mode_use_offsets, mode_use_annotations]:
        context_manager = ContextManagerPDTB2()
        annotations = context_manager.add_context(annotations, raw_contents,
                                                  consider_all=FLAG_consider_all,
                                                  emphasise_connectives=True,
                                                  context_mode=mode)
    # elif mode == mode_use_joen:
    #     context_manager = ContextManagerPDTB2()
    #     annotations = context_manager.add_context(annotations, raw_contents,
    #                                               consider_all=FLAG_consider_all,
    #                                               emphasise_connectives=True,
    #                                               context_mode=mode,
    #                                               context_size=context_size)

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
            elif mode==1:
                if context_size > 0: #Need to the prune context as needed
                    #1 < context_size < 99: means amount of gold relationships to use
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

                        offset = context_size
                        if offset > len(chained_context):
                            offset = len(chained_context)

                        some_context = chained_context[-offset:]  #context_size is number of context sentences to use

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
            if context_size > 0:
                #have to use Wei Liu's relation strings (so no ___ before and after the type label
                if len(sample["context_full_procecssed_chain"]) > 0  and sample["relation_type"]=="Implicit":
                    print(f"-----------\n {json.dumps(sample, indent=3)} \n -----------------")

            #finalise result
            result.append(sample)

    print(f"SUMMARY: Context len dist: {context_len_dist}")  #print to stdout distribution of context offset lengths for this preprocessing job
    return result

