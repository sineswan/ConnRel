from data_wrapper.pdtb_data_wrapper import *

class ContextManagerPDTB2:

    def add_context(self, doc_id, annotations, raw_text, consider_all=False, emphasise_connectives=False, context_mode=0):
        """
        This method loops through all the annotations and collects context, noting that context can be carried across
        annotations.
        """

        # assuming annotations are in order
        arg1s = {}
        arg2s = {}

        dependencies = {}
        dependency_offsets = {}

        mode1_stats = {
            "found": 0,
            "not_found": 0,
            R_ENTREL: 0,
            R_IMPLICIT: 0,
            R_EXPLICIT: 0,
            R_NOREL: 0,
            R_ALTLEX: 0
        }

        for i, annotation in enumerate(annotations):
            annotation["context"] = None

            # save args to internal dicts
            arg1 = annotation[R_ARG1]["arg_text"]
            arg2 = annotation[R_ARG2]["arg_text"]
            # Find the earliest point to trackback to find context
            arg1_start = annotation[R_ARG1]["arg_span_list"][0][0]  # 1st element, 1st offset
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
            # context_mode = 0
            if raw_text:  # so assuming there's original content to get context

                context = ""
                # print(f"Arg start chars: {arg1_start} {arg2_start}")
                arg_start_min = min(arg1_start, arg2_start)
                # print(f"min: {arg_start_min}")
                context = raw_text[:arg_start_min]

                # print(f"Arg start chars: {arg1_start} {arg2_start}: {context}")
                annotation["context"]["raw"] = context

            # Mode 1: use gold context
            if context_mode==1:

                found_match = None
                for an_arg2 in arg2s.keys():
                    if arg1 in an_arg2 or an_arg2 in arg1:  # some nested substring exists:
                        found_match = an_arg2

                if found_match:
                    # print(f"FOUND prior dependency: ARG1: {arg1}, found_match: {found_match}, ARG2: {arg2} ")
                    mode1_stats["found"] += 1

                    # We loop over all data points with this prior arg2 which might break linear order of text but this is rare.
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
                            # find the prior_arg and conn offsets and find the outer set (maximal string)

                            prior_connective_positions = None
                            if prior_discourse_type == R_IMPLICIT:
                                # it's a nominal char position where the connective would be inserted.
                                prior_connective_position = prior_dep["string_pos"]
                                if emphasise_connectives:
                                    if prior_connective_position < prior_arg_start:
                                        candidate_prior_arg = " " + prior_connective + " " + candidate_prior_arg
                                    else:
                                        candidate_prior_arg = candidate_prior_arg + " " + prior_connective + " "

                                    # if prior_connective_position < prior_arg_start:
                                    #     candidate_prior_arg = " # " + prior_connective + " @ " + candidate_prior_arg
                                    # else:
                                    #     candidate_prior_arg = candidate_prior_arg + " # " + prior_connective + " @ "

                            else:
                                # could be a range
                                prior_connective_position_tuple = prior_dep["main_span_list"]
                                prior_connective_positions = prior_connective_position_tuple[0]
                                prior_connective_start = prior_connective_positions[0]

                                # prior_connective_positions are now set

                                # Connective could come before arg1: e.g., Although ARG1 ... ARG2
                                earliest_char_pos = (prior_arg_start) if \
                                    (prior_arg_start < prior_connective_start) else prior_connective_start

                                # always use prior_arg_end because if the connective comes after it is the start of a new sent
                                candidate_prior_arg = raw_text[earliest_char_pos:prior_arg_end]
                                # if prior_connective_position[1] > prior_arg_end:

                                if emphasise_connectives:
                                    if prior_connective_start < prior_arg_start:
                                        candidate_prior_arg = " " + prior_connective + " " + candidate_prior_arg
                                    else:
                                        candidate_prior_arg = candidate_prior_arg + " " + prior_connective + " "

                                    # if prior_connective_position < prior_arg_start:
                                    #     candidate_prior_arg = " #_ " + prior_connective + " _@ " + candidate_prior_arg
                                    # else:
                                    #     candidate_prior_arg = candidate_prior_arg + " #_ " + prior_connective + " _@ "

                        mode1_stats[prior_discourse_type] += 1

                        # find preceding (accumulated) dependencies
                        if prior_arg in dependencies.keys():
                            # need to iterate to *copy* content (i.e., duplicate) to new dep_context for THIS data point
                            for deps in dependencies[prior_arg]:
                                dep_context.append(deps)
                            for deps_start, deps_end in dependency_offsets[prior_arg]:
                                dep_context_offsets.append((deps_start, deps_end))  # duplicate tuple

                        # Only use (explicit or implicitly marked) discourse relationships
                        if (consider_all and prior_discourse_type in annot_exists) or \
                                (prior_discourse_type in annot_has_relationship):
                            # print(f"prior connective: {prior_connective}")
                            dep_context.append(candidate_prior_arg)
                            dep_context_offsets.append((earliest_char_pos, latest_char_pos))

                    # print(f"len(chained_context): {len(dep_context)}: {dep_context}\n")
                    annotation["context"]["chained"] = dep_context
                    annotation["context"]["chained_offsets"] = dep_context_offsets
                    annotation["context"]["chained_source_ids"] = arg2s[found_match]

                    # accumulate dependencies for this matched arg1
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