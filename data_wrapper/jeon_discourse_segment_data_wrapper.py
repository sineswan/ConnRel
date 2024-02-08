import csv, argparse, json, ast

class JeonSegmentReader:

    def __init__(self, sentence_segment_filename, discourse_segments_filename, docid_mappings=None):
        self.sentences_filename = sentence_segment_filename
        self.discourse_segments_filename = discourse_segments_filename
        self.sentences = None
        self.discourse_segments = None
        self.discourse_segments_inverted_index = None

        self.docid_mappings = None
        if docid_mappings:
            self.docid_mappings = json.load(open(docid_mappings))

        self.sentences = self.reader_sentences(sentence_segment_filename, self.docid_mappings)
        self.discourse_segments = self.reader_discourse_segments(discourse_segments_filename, self.docid_mappings)
        self.cleanup()  #needed to repair discourse segments if segment data is missing

        #create discourse segment inverted index
        self.discourse_segments_inverted_index = self.create_segments_inverted_index()

    def create_segments_inverted_index(self):
        result = {}   #key: doc_id, value={ sent_id: segment_id, .... }
        for doc_id in self.discourse_segments.keys():
            segments = self.discourse_segments[doc_id]["segments"]
            inverted_index = {} #{ sent_id: segment_id, .... }
            for segment_id in segments.keys():
                sentences = self.discourse_segments[doc_id]["segments"][segment_id]
                for sent_id in sentences:
                    inverted_index[sent_id] = segment_id
            result[doc_id] = inverted_index
        return result

    def cleanup(self):
        print(f"size sents: {len(self.sentences.keys())}, size segments: {len(self.discourse_segments.keys())}")

        for key in self.sentences.keys():
            num_sents = self.sentences[key]["num_sents"]

            sent_ids = self.discourse_segments[key]["sent_ids"]

            if not num_sents == len(sent_ids):
                # print(
                #     f"id: {key}, num_sents: {num_sents}, size sent_ids:{len(sent_ids)}, --- {self.discourse_segments[key]}")

                # create dummy segments
                new_segments = {}
                new_sent_ids = []
                for i, sent_id in enumerate(range(num_sents)):
                    new_segments[i] = [sent_id]
                    new_sent_ids.append(sent_id)
                self.discourse_segments[key] = {"segments": new_segments, "sent_ids": new_sent_ids}

    def reader_sentences(self, sentence_segment_filename, id_mapping=None):

        result = {}  #key:id, value={"num_sents":<d>, "sentences":[list of string] .... }
        with open(sentence_segment_filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                id = f"{int(row[0]):04d}"  #interpet string as number in 4 digits but finally as STRING
                if id_mapping:
                    id = id_mapping[str(int(id))]        #mapping ids are numbers as strings with no leading zeros

                num_sents = int(row[1])
                sentences = ast.literal_eval(row[2])
                result[id] = {"num_sents":num_sents, "sentences":sentences}
                line_count += 1
            print(f'Processed {line_count} lines.')
        return result


    def reader_discourse_segments(self, discourse_segments_filename, id_mapping=None):

        result = {}  #key:doc_id, value={"segments": {seg_id:[list of sent_ids] .... }, "sent_ids": [list of nums] }
        with open(discourse_segments_filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                id = f"{int(row[0]):04d}"  #interpet string as number in 4 digits but finally as STRING
                if id_mapping:
                    id = id_mapping[str(int(id))]        #mapping ids are numbers as strings with no leading zeros
                segments_stringified = row[2]  #skip info in cols 1,3

                # print(f"segment_string: {segments_stringified}")

                segments = ast.literal_eval(segments_stringified)
                sent_ids = []
                for segment_key in segments.keys():
                    sent_ids.extend(segments[segment_key])
                result[id] = {"segments": segments, "sent_ids":sent_ids}

                line_count += 1
            print(f'Processed {line_count} lines.')
        return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sentences_input", required=True)
    parser.add_argument("--segments_input", required=True)
    args = parser.parse_args()

    reader = JeonSegmentReader(args.sentences_input, args.segments_input)
    # print(f"Sentences: {reader.sentences.keys()}")
    # print(f"Segments: {reader.discourse_segments.keys()}")

    print(f"size sents: {len(reader.sentences.keys())}, size segments: {len(reader.discourse_segments.keys())}")

    for key in reader.sentences.keys():
        num_sents = reader.sentences[key]["num_sents"]

        sent_ids = reader.discourse_segments[key]["sent_ids"]

        if not num_sents == len(sent_ids):
            print(
                f"id: {key}, num_sents: {num_sents}, size sent_ids:{len(sent_ids)}, --- {reader.discourse_segments[key]}")

            # create dummy segments
            new_segments = {}
            new_sent_ids = []
            for i, sent_id in enumerate(range(num_sents)):
                new_segments[i] = [sent_id]
                new_sent_ids.append(sent_id)
            reader.discourse_segments[key] = {"segments": new_segments, "sent_ids": new_sent_ids}


    print(f"{json.dumps(reader.sentences, indent=3)}")
    print(f"{json.dumps(reader.discourse_segments_inverted_index, indent=3)}")