import json


class SpanUnentangler:

    def make_non_overlapping_context_chain(self, chain, chain_offsets):

        '''Note: span_ids here will be used to index the chain and chain_offsets arrays.  Note that the chain_offsets are to
        the original text NOT the text in the chains (which may contain extra markup).

        Algorithm:
        - Start with the longest span as the main boundary

        and in sorted order of remaining spans (by start_offset)
        - EXTERNAL Check if span in main boundary, if not (sorted) add span to kept_spans, and increase boundary.
        - INTERNAL (island, subsumed, partially overlapping):
            Case 1. for added_span in sorted order(kept_spans):
                while added_span_start < current span_start
                    Check if current_span_start in added_span.  If so, check if current_span_end also in added span.
                        If so, ignore current_span
                        If not, extend end of added span (and repair next added_span if needed)
            Case 2. Otherwise, the start is new, but end could be in next span
                    check if current_span_end in added_span. if so, extend start of added span.
            Case 3 [island].  Add current span to kept_spans

        '''

        # print(f"INPUTS: \n {json.dumps(chain, indent=3)} \n {chain_offsets}")

        # 1. Prepare sorted views of data: Sort spans by size and keep a sorted order of span_starts

        span_sizes = {}  # key=size, value=[array of span_ids]
        span_starts = {}  # key=span_start, value = [array of span_ids]

        for span_id, span in enumerate(chain_offsets):

            # calculate and store lengths
            length = span[1] - span[0]  # assume start < end
            if length not in span_sizes.keys():
                span_sizes[length] = [span_id]
            else:
                span_sizes[length].append(span_id)

            # keep track of starts
            start = span[0]
            if start not in span_starts.keys():
                span_starts[start] = [span_id]
            else:
                span_starts[start].append(span_id)

        # Create boundary (pop largest)
        kept_spans = {}  # key = start, value=span
        max_span_length = max(span_sizes.keys())
        a_big_span_id = span_sizes[max_span_length][0]  # could be multiple, must be at least one, just take first.
        boundary = chain_offsets[a_big_span_id]

        # print(f"max_span_length: {max_span_length}, boundary: {boundary}")

        kept_spans[boundary[0]] = {"start": boundary[0], "end": boundary[1], "text":chain[a_big_span_id]}

        for a_span_size in sorted(span_sizes.keys(), reverse=True):  #must iterate outer loop by span size to limit mergers later

            # print(f"\na_span_size: {a_span_size}")

            for span_id in span_sizes[a_span_size]:
                span_offset = chain_offsets[span_id]

                # print(f"span_id: {span_id}")

                # CASE 0. [External]  Non-overlapping
                initial_overlap = self.has_some_overlap_spans(boundary, span_offset)
                # print(f"initial_overlap: {initial_overlap}")

                if not initial_overlap:  #not overlapping

                    # print(f"OUTCOME: simple insertion outside boundary")

                    kept_spans[span_offset[0]] = {"start":span_offset[0], "end":span_offset[1], "text":chain[span_id]}
                else:

                    # print(f"Entering 2nd branch")

                    #CASE 1-3:  Compare to all already added spans
                    sorted_span_start_keys = sorted(kept_spans.keys())
                    sorted_span_start_keys_ptr = 0
                    added_span_start = sorted_span_start_keys[sorted_span_start_keys_ptr]

                    # print(f"sorted_span_start_keys: {sorted_span_start_keys}")

                    # CASE 1. [partial overlap, start maybe covered by existing span.  Covers complete covering too (skipped)
                    #Inner loop must be ordered by start_offset
                    FLAG_case_closed = False
                    while not FLAG_case_closed \
                            and sorted_span_start_keys_ptr < len(sorted_span_start_keys) \
                            and added_span_start <= span_offset[0] \
                            :

                        # print(f"entering while loop: {sorted_span_start_keys_ptr}")

                        if added_span_start == -1:
                            #skip this.  This span was merged into an earlier block. Technically, shouldn't be required
                            #since FLAG_case_closed will be TRUE if the next block is amended to be -1
                            sorted_span_start_keys_ptr += 1
                            added_span_start = sorted_span_start_keys[sorted_span_start_keys_ptr]
                            continue

                        # print(f"sorted_span_start_keys_ptr: {sorted_span_start_keys_ptr}")

                        #otherwise, consider this added_span for overlaps.
                        added_span_end = kept_spans[added_span_start]["end"]
                        added_span = (added_span_start, added_span_end)

                        overlap = self.has_some_overlap_spans(added_span, span_offset)

                        #maybe identical span or subsumed completely, or partial (positive case) so set flag to TRUE
                        # if overlap == 2 nothing happens, existing added span is fine.
                        if overlap >= 1:
                            #overlap found for this case
                            FLAG_case_closed = True


                            # so added_span MUST be extended; This could mean the current added_span "crashes" into
                            # the next added_span, in which case they need to be merged.
                            if overlap == 1: #so some extension needed (and span2 comes AFTER span1; Different from -1 case!!)

                                print(f"OUTCOME: merging overlap 1: span_offset: {span_offset}, chain: {chain}, offsets: {chain_offsets}")


                                kept_spans[added_span_start]["end"] = span_offset[1]  #the extension because overlap==1

                                #20231218: don't seem to run into this for PDTB2  ... but we do for PDTB3
                                kept_spans[added_span_start]["text"] = "FIXME1"

                                #check that next added_span is still fine
                                if len(sorted_span_start_keys) > sorted_span_start_keys_ptr + 1:  #check there is a next
                                    next_added_span_start = sorted_span_start_keys[sorted_span_start_keys_ptr + 1]
                                    if span_offset[1] > next_added_span_start:

                                        #next span needs to be merged into this one.
                                        next_added_span = kept_spans[next_added_span_start]
                                        kept_spans[added_span_start]["end"] = next_added_span["end"]  # the extension because overlap==1

                                        # update text: don't seem to run into this PDTB2
                                        kept_spans[added_span_start]["text"] = "FIXME2"

                                        #now clear the next added_span
                                        sorted_span_start_keys[sorted_span_start_keys_ptr + 1] = -1  #-1 means skip this
                            else:
                                # print(f"OUTCOME: skipping overlap 2")
                                #Note that because we start with the largest span, we can't get overlap = -2
                                pass

                        else:
                            #maintain loop variables
                            sorted_span_start_keys_ptr += 1
                            added_span_start = sorted_span_start_keys[sorted_span_start_keys_ptr]

                    #CASE 2 and 3. All considered kept_spans (smaller start offset) don't contain this new span.  But maybe end
                    # overlaps with next span (which is very offset that is larger).  Note can only go into the next span
                    # we sorted by size and by definition, any considered spans must be equal or larger than this one.
                    if not FLAG_case_closed:
                        while added_span_start == -1 and sorted_span_start_keys_ptr < len(sorted_span_start_keys):
                            # maintain loop variables
                            sorted_span_start_keys_ptr += 1
                            added_span_start = sorted_span_start_keys[sorted_span_start_keys_ptr]

                        #so now added_span_start should be the next one which has larger start_offset

                        added_span_end = kept_spans[added_span_start]["end"]
                        added_span = (added_span_start, added_span_end)
                        overlap = self.has_some_overlap_spans(added_span, span_offset)

                        #CASE 2: some overlap
                        if overlap == -1:

                            # print(f"OUTCOME: merging overlap -1")

                            # start_offset by def is outside added_span but end is inside. (so Span2 comes BEFORE Span1)
                            FLAG_case_closed = True #set to TRUE, although we don't need it anymore.  Just for consistency

                            #update the added_span start
                            sorted_span_start_keys[sorted_span_start_keys_ptr] = span_offset[0]  #adjust value
                            #create new span entry (requires new start offset key)
                            merged_text = kept_spans[added_span_start]["text"]
                            diff_start = added_span_start - span_offset[0]
                            additional_text = chain[span_id][:diff_start]
                            merged_text += additional_text
                            kept_spans[span_offset[0]] = {
                                "start": span_offset[0],
                                "end": kept_spans[added_span_start]["end"],
                                "text": merged_text
                            }
                            kept_spans.pop(added_span_start)  #old span must be deleted

                        #CASE 3: no overlap, this is a simple insertion (without changing the boundaries)
                        elif overlap == 0:

                            # print(f"OUTCOME: simple insertion within boundary")

                            FLAG_case_closed = True #set to TRUE, although we don't need it anymore.  Just for consistency

                            kept_spans[span_offset[0]] = {"start":span_offset[0], "end":span_offset[1], "text":chain[span_id]}

                #Handled the span_offset, now adjust boundaries if needed
                boundary = self.maintain_boundary(boundary, span_offset)

        return kept_spans, boundary

    def maintain_boundary(self, boundary, span_offset):

        # print(f"boundary: {boundary}, span_offset: {span_offset}")

        # maintain boundary
        new_start = boundary[0]
        new_end = boundary[1]
        if span_offset[0] < new_start:
            new_start = span_offset[0]
        if span_offset[1] > new_end:
            new_end = span_offset[1]

        return (new_start, new_end)

    def has_some_overlap_spans(self, span1, span2):
        '''
        spans are (start, end) shape
        return: 0: no overlap, 1: partial, 2: complete

        Notes:
            - if NEGATIVE, then span2 < span1 (when overlapping)
            - if POSITIVE, then span1 < span2 (when overlapping)
        '''

        # print(f"span1: {span1}, span2: {span2}")

        if span2[1] <= span1[0] or span2[0] >= span1[1]:
            return 0
        elif span2[0] >= span1[0] and span2[1] <= span1[1] :
            return 2
        elif span1[0] >= span2[0] and span1[1] <= span2[1]:
            return -2
        elif span2[0] >= span1[0]:
            return 1
        else:
            return -1


if __name__ == "__main__":
    '''
    This is testing code for this class based on examples from PDTB2 and my modification of Wei Liu's 2023 code
    '''
    chains1 =  ['that his new album, "Inner Voices," had just been released, that his family was in the front row #_ and _@ ',
               "and that it was his mother's birthday #_ so _@ ",
               'Clad in his trademark black velvet suit, the soft-spoken clarinetist announced that his new album, "Inner Voices," had just been released, that his family was in the front row, and that it was his mother\'s birthday, so he was going to play her favorite tune from the record # then @ ']
    #& He launched into Saint-Saens's "The Swan" from "Carnival of the Animals," a favorite encore piece for cellists, with lovely, glossy tone and no bite
    # then @
    # he offered the second movement from Saint-Saens's Sonata for Clarinet, a whimsical, puckish tidbit that reflected the flip side of the Stoltzman personality

    chain_offsets1 = [(1543, 1639), (1641, 1678), (1464, 1737)]
    chains2 = ['that his new album, "Inner Voices," had just been released, that his family was in the front row #_ and _@ ',
     "and that it was his mother's birthday #_ so _@ ",
     'Clad in his trademark black velvet suit, the soft - spoken clarinetist announced that his new album, "Inner Voices," had just been released, that his family was in the front row, and that it was his mother\'s birthday, so he was going to play her favorite tune from the record # then @ ',
     'He launched into Saint-Saens\'s "The Swan" from "Carnival of the Animals," a favorite encore piece for cellists, with lovely, glossy tone and no bite #_ then _@ '] \

    chain_offsets2 = [(1543, 1639), (1641, 1678), (1464, 1737), (1739, 1887)]

    chains3 = ['that his new album, "Inner Voices," had just been released, that his family was in the front row #_ and _@ ',
     "and that it was his mother's birthday #_ so _@ ",
     'Clad in his trademark black velvet suit, the soft-spoken clarinetist announced that his new album, "Inner Voices," had just been released, that his family was in the front row, and that it was his mother\'s birthday, so he was going to play her favorite tune from the record # then @ ',
     'He launched into Saint-Saens\'s "The Swan" from "Carnival of the Animals," a favorite encore piece for cellists, with lovely, glossy tone and no bite #_ then _@ ',
     'Then #_ as if _@ ',
     "Then, as if to show that he could play fast as well, he offered the second movement from Saint-Saens's Sonata for Clarinet, a whimsical, puckish tidbit that reflected the flip side of the Stoltzman personality #_ and _@ "]

    chain_offsets3 = [(1543, 1639), (1641, 1678), (1464, 1737), (1739, 1887), (1889, 1893), (1889, 2098)]

    chains4 = ['Is this the future of chamber music # in particular @ ',
               'but can audiences really enjoy them #_ if _@ ',
     'but can audiences really enjoy them only if the music is purged of threatening elements, served up in bite-sized morsels and accompanied by visuals # and @ ',
     "What's next # for instance @ "]

    chain_offsets4 = [(5289, 5324), (5402, 5437), (5402, 5549), (5551, 5562)]

    chains5 = [
        'On a commercial scale, the sterilization of the pollen-producing male part has only been achieved in corn and sorghum feed grains #_  _@ ',
        "That's #_ because _@ ",
        "That's because the male part, the tassel, and the female, the ear, are some distance apart on the corn plant # consequently @ ",
        'In a labor-intensive process, the seed companies cut off the tassels of each plant, making it male sterile # then @ ']
    chain_offsets5 = [(844, 973), (975, 981), (975, 1083), (1085, 1191)]

    chains6 = ['No wonder # because @ ', 'We were coming down straight into their canal # because @ ',
     "that you can't steer #_ and _@ ", "that you can't steer., And neither can your pilot # in fact @ ",
     'You can go only up or down #_  _@ ', 'Most balloonists seldom go higher than 2,000 feet #_ and _@ ']

    chain_offsets6 = [(3894, 3903), (3905, 3950), (4001, 4021), (4001, 4049), (4051, 4077), (4242, 4291)]

    chains = chains6
    chain_offsets = chain_offsets6

    entangler = SpanUnentangler()
    kept_spans = entangler.make_non_overlapping_context_chain(chains, chain_offsets)

    print(f"kept_spans: {kept_spans}")

