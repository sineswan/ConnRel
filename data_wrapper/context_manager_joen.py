from data_wrapper.context_manager_pdtb_default import ContextManagerPDTB2
from data_wrapper.pdtb_data_wrapper import *
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

    def add_context_single_datapoint(self, doc_id, annotation, arg1, context_mode=2):
        annotation["context"] = None

        # Pseudocode:
        # 1. find best Jeon sentence that aligns with arg1
        # 2. Mode A: Retrieve the segment that the sentence belongs to.
        # 3.         Retrieve the prior n sentences from the segment.
        # 4. Mode B: Retrieve the prior n sentences in the document.

        # 1. find best Jeon sentence that aligns with arg1
        sent_id, matched_sent = self.find_aligned_sentence(arg1, doc_id)

        # print(f"TRACE: target:{arg1}, best: {matched_sent}, id:{sent_id}")

        # 2. Mode A: Retrieve the segment that the sentence belongs to.
        seg_id = self.jeon_segment_reader.discourse_segments_inverted_index[doc_id][sent_id]

        sentences = None
        if context_mode == 2:
            # mode A
            segment_sent_ids = self.jeon_segment_reader.discourse_segments[doc_id]["segments"][seg_id]
            sentences = []
            org_sentences = self.jeon_segment_reader.sentences[doc_id]["sentences"]
            for seg_sent_id in segment_sent_ids:
                if seg_sent_id == sent_id:
                    break  # assuming seg_sent_ids are in ascending order
                else:
                    sentences.append(org_sentences[seg_sent_id])
            annotation["context"] = {}
            annotation["context"]["chained"] = sentences  # everything up to the aligned sentence

        elif context_mode == 3:
            # mode B
            sentences = self.jeon_segment_reader.sentences[doc_id]["sentences"]

            # 3/4 Retrieve prior sentences from which even sentence list is used
            if sent_id > -1:
                end_slice = sent_id
                # if end_slice > len(sentences):
                #     end_slice = -1
                annotation["context"] = {}
                annotation["context"]["chained"] = sentences[:end_slice]  # everything up to the aligned sentence
            else:
                print(f"TRACE: no alignment: target:{arg1}, best: {matched_sent}, id:{sent_id}")

        else:
            raise Exception(f"unknown context mode: {context_mode}")

        return annotation

    def add_context(self, doc_id, annotations, raw_text, consider_all=False, emphasise_connectives=False, context_mode=0):
        """
        context_mode == 2: Mode A: use context from Jeon's segmentations
        context_mode == 3: Mode B: just use context from sentence segmentation
        """

        final_annotations = []
        for i, annotation in enumerate(annotations):
            arg1 = annotation[R_ARG1]["arg_text"]
            amended_annotation = self.add_context_single_datapoint(doc_id=doc_id, annotation=annotation, arg1=arg1, context_mode=context_mode)
            final_annotations.append(amended_annotation)


        return final_annotations, None  #second return value is NULL stats record