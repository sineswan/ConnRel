import argparse, json, csv, os


def get_disrpt_dir_structure(disrpt_subdataset):
    disrpt_dir_structure = {
        "tokens": {
            "dev": f"{disrpt_subdataset}/{disrpt_subdataset}_dev.tok",
            "test": f"{disrpt_subdataset}/{disrpt_subdataset}_test.tok",
            "train": f"{disrpt_subdataset}/{disrpt_subdataset}_train.tok"
        },
        "conllu": {
            "dev": f"{disrpt_subdataset}/{disrpt_subdataset}_dev.conllu",
            "test": f"{disrpt_subdataset}/{disrpt_subdataset}_test.conllu",
            "train": f"{disrpt_subdataset}/{disrpt_subdataset}_train.conllu"
        },
        "rels": {
            "dev": f"{disrpt_subdataset}/{disrpt_subdataset}_dev.rels",
            "test": f"{disrpt_subdataset}/{disrpt_subdataset}_test.rels",
            "train": f"{disrpt_subdataset}/{disrpt_subdataset}_train.rels"
        }
    }
    return disrpt_dir_structure

def fixes(id):
    if id == f"GUM_bio_byron.190-193.194-198,203-217":
        return {
            "doc":"GUM_bio_byron",
            "unit1_toks":"190-193",
            "unit2_toks":"194-198,203-217",
            "unit1_txt":"His mother wrote ,",
            "unit2_txt":"\" He has no indisposition <*> but love , desperate love , the worst of all maladies in my opinion .",
            "s1_toks":"190-234",
            "s2_toks":"190-234",
            "unit1_sent":"His mother wrote , \" He has no indisposition that I know of but love , desperate love , the worst of all maladies in my opinion . In short , the boy is distractedly in love with Miss Chaworth . \" [ 6 ]",
            "unit2_sent":"His mother wrote , \" He has no indisposition that I know of but love , desperate love , the worst of all maladies in my opinion . In short , the boy is distractedly in love with Miss Chaworth . \" [ 6 ]",
            "dir":"1>2",
            "orig_label":"attribution-positive",
            "label":"attribution-positive"
        }
    return None

def read_disrpt_rels(filename):
    # open .tsv file
    data = []
    #Read the relations
    if os.path.exists(filename):
        with open(filename, encoding="utf-8") as file:
            csv_reader = csv.DictReader(file, delimiter="\t", quoting=csv.QUOTE_ALL)
            for row in csv_reader:
                id = f"{row['doc']}.{row['unit1_toks']}.{row['unit2_toks']}"
                # print(f"id: {id}")
                fixed = fixes(id)
                if fixed:
                    data.append(fixed)
                else:
                    # print(row)
                    data.append(row)

    #Read the full text
    docs = {}  #key=doc_id, val=[{"sent":<str>, "id":<str>} ... ]
    sentences_tmp = {} #key=start_pos, val=sentence
    last_doc_id = None
    for datum in data:
        doc_id = datum["doc"]

        if last_doc_id and not doc_id == last_doc_id:
            #change in doc_id, so store the last document
            sentences = []
            for sent_start in sorted(sentences_tmp.keys()):
                sentences.append({"sent":sentences_tmp[sent_start],
                                  "id":f"{last_doc_id}."+"{:03d}".format(sent_start)})
            docs[last_doc_id] = sentences
            sentences_tmp = {}

        last_doc_id = doc_id
        sentence1 = datum["unit1_sent"]
        sentence2 = datum["unit2_sent"]
        sent1_start_str = datum["s1_toks"].split("-")[0]
        sent2_start_str = datum["s2_toks"].split("-")[0]
        # print(f"doc_id: {doc_id}, sent1_pos: {sent1_start_str}, sent2_pos: {sent2_start_str}")

        try:
            sentence1_start = int(sent1_start_str)
            sentence2_start = int(sent2_start_str)

            for sent_start, sentence  in [(sentence1_start, sentence1), (sentence2_start, sentence2)]:
                if not sent_start in sentences_tmp.keys():
                    sentences_tmp[sent_start] = sentence
        except Exception as e:
            print(f"Problem with datum: {datum}")


    #store last doc
    if last_doc_id:
        sentences = []
        for sent_start in sorted(sentences_tmp.keys()):
            sentences.append({"sent": sentences_tmp[sent_start],
                              "id": f"{last_doc_id}." + "{:03d}".format(sent_start)})
        docs[last_doc_id] = sentences

    return data, docs

def read_disrpt_connllu_for_raw_text(filename):
    docs = {} #key=doc_id, value= [ {"sent":<str>, "id":<str>} ... ]
    with open(filename, "r") as file:
        lines = file.readlines()
        sent_id = None
        doc_id = None
        text = None
        doc_sentences = []

        newdoc_prefix = "# newdoc_id = "
        sentid_prefix = "# sent_id = "
        text_prefix = "# text = "
        for i,line in enumerate(lines):
            if line.startswith(sentid_prefix):
                if lines[i+1].startswith(newdoc_prefix):
                    #save old doc
                    if len(doc_sentences)>0:
                        docs[doc_id] = doc_sentences

                    #start new doc
                    doc_sentences = []
                    doc_id = lines[i+1][len(newdoc_prefix)-1:].strip()
                sent_id = line[len(sentid_prefix)-1:].strip()
            elif line.startswith(text_prefix):
                text = line[len(text_prefix)-1:].strip()
                doc_sentences.append({
                    "sent":text,
                    "id":sent_id
                })

                #reset sentence info
                text = None
                sent_id = None

        ##save old doc
        docs[doc_id] = doc_sentences

    return docs

def get_first_word(string):
    first_word = string.lower().split(" ")[0]  # take first word, make lowercase
    return  first_word

def get_tail(string):
    return " ".join(string.lower().split(" ")[1:])  # remove first word, make lowercase

def convert(relation,  relations, raw_texts,
            context_mode=None, context_size=1, label_level=0):

    id = relation["doc"]+"."+relation["unit1_toks"]+"."+relation["unit2_toks"]

    arg1 = relation["unit1_txt"]
    arg2 = relation["unit2_txt"]
    if relation["dir"] == "1>2":
        arg1 = relation["unit2_txt"]
        arg2 = relation["unit1_txt"]
    # print(id)

    #initialise final record
    result = {
        "id":id,
        "relation_class": None,
        "arg1": arg1,
        "arg1_org": arg1,
        "arg2": get_tail(arg2),
        "conn": get_first_word(arg2),
        "arg2_org": arg2,
        "relation_type": "Implicit",
        "context": None,
        "truncation_length": None,
        "arg1_org_len": len(arg1),
        "context_mode": context_mode,
        "context_size": context_size,
        "context_provenance": None
    }
    corrected_label = relation["label"]
    if corrected_label:
        if "-" in corrected_label:
            corrected_label = corrected_label.split("-")[label_level]
        result["relation_class"] = corrected_label
    else:
        result["relation_class"] = "elab"  #hack
        print(f"WARNING: setting rel_class to dummy ELAB: data: {result}")

    if context_mode==3:
        #mode3: always add preceding sentence.
        doc_id = id.split(".")[0]
        sentences = raw_texts[doc_id]
        arg1_sentence = relation["unit1_sent"]
        matched_sentence = None
        cursor = -1
        for i, sentence in enumerate(sentences):
            target_sentence = sentence["sent"]
            cursor = i
            if arg1_sentence.strip()==target_sentence.strip():
                matched_sentence =target_sentence
                break   #assume 1 match only
        if not matched_sentence:
            print(f"Didn't find match for {doc_id} {arg1_sentence}")
            0/1
        else:
            context = ""
            if cursor>0 and cursor<len(sentences):
                context = sentences[cursor - 1]["sent"]
            result["arg1"] = context + " ... " + arg1
            result["context"] = context
            provenance = sentences
            result["context_provenance"] = provenance


    return result

if __name__ == "__main__":
    print(f"Running converter of DISRPT rel files to ConnRel json files")
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_dir", required=True, help="DISRPT dir for component data set")
    args = parser.parse_args()
    filename = "eng.dep.covdtb_dev.rels"
    result = read_disrpt_rels(os.path.join(args.dataset_dir, filename))

    filename = "eng.dep.covdtb_dev.conllu"
    result = read_disrpt_connllu_for_raw_text(os.path.join(args.dataset_dir, filename))

    print (f"raw file: {len(result.keys())}")