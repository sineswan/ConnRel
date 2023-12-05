from data_wrapper.context_manager_pdtb2_default import ContextManagerPDTB2
from data_wrapper.pdtb2_data_wrapper import *
from data_wrapper.jeon_discourse_segment_data_wrapper import JeonSegmentReader

import difflib

class ContextManagerJoen(ContextManagerPDTB2):
    """
    This subclass will use output files created by the Sungho Joen code base, which effectively automatically segments
    some text and provides dependencies between sentences, theoretically based on Centering Theory.
    """

    def __init__(self, jeonSegmentReader):
        super().__init__()
        self.jeon_segment_reader = jeonSegmentReader

    def find_aligned_sentence(self, fragment, doc_id):
        sentences = self.jeon_segment_reader.sentences[doc_id]["sentences"]

        # find best (first element in list), may need to set cutoff to always get response
        try:
            best_match = difflib.get_close_matches(fragment, sentences, n=1, cutoff=0)[0]
        except Exception as e:
            print(f"TRACE -- fragrment: {fragment}, sentences: {sentences}")
            raise e



        # print(f"TRACE -- fragrment: {fragment}, best match: {best_match}")

        best_i = -1
        for i, sentence in enumerate(sentences):
            if sentence==best_match:
                best_i = i
                break

        if best_i==-1:
            raise Exception(f"Best_i is -1: {fragment}, {doc_id}")

        return best_i, best_match


    def add_context(self, doc_id, annotations, raw_text, consider_all=False, emphasise_connectives=False, context_mode=0):
        """
        context_mode == 2: Mode A: use context from Jeon's segmentations
        context_mode == 3: Mode B: just use context from sentence segmentation
        """

        for i, annotation in enumerate(annotations):
            annotation["context"] = None

            # save args to internal dicts
            arg1 = annotation[R_ARG1]["arg_text"]
            arg2 = annotation[R_ARG2]["arg_text"]
            # Find the earliest point to trackback to find context
            arg1_start = annotation[R_ARG1]["arg_span_list"][0][0]  # 1st element, 1st offset
            arg2_start = annotation[R_ARG2]["arg_span_list"][0][0]  # 1st element, 1st offset

            #Pseudocode:
            # 1. find best Jeon sentence that aligns with arg1
            # 2. Mode A: Retrieve the segment that the sentence belongs to.
            # 3.         Retrieve the prior n sentences from the segment.
            # 4. Mode B: Retrieve the prior n sentences in the document.

            # 1. find best Jeon sentence that aligns with arg1
            sent_id, matched_sent = self.find_aligned_sentence(arg1, doc_id)

            # print(f"TRACE: target:{arg1}, best: {matched_sent}, id:{sent_id}")

            #mode B
            sentences = self.jeon_segment_reader.sentences[doc_id]["sentences"]
            if sent_id>-1:
                end_slice = sent_id
                if end_slice > len(sentences):
                    end_slice = -1
                annotation["context"] = {}
                annotation["context"]["chained"] = sentences[:end_slice]  #everything up to the aligned sentence
            else:
                print(f"TRACE: no alignment: target:{arg1}, best: {matched_sent}, id:{sent_id}")

        return annotations