import argparse, json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsondata", required=True)
    args = parser.parse_args()

    data_lines = []
    with open(args.jsondata, "r") as f:
        for line in f.readlines():
            data_lines.append(line)

    hist = {

    }
    for i,line in enumerate(data_lines):
        data = json.loads(line)
        data_type = data["relation_type"]
        data_class = data["relation_class"]

        if not data_type in hist.keys():
            hist[data_type] = {}


        if not data_class in hist[data_type].keys():
            hist[data_type][data_class] = {
                "context":{}, "no_context":{}
            }

        is_context = False
        if "context" in data.keys():
            if not data["context"] == "":
                is_context = True
        else:
            parts = data["arg1"].strip().split(" ... ")
            if len(parts) > 1\
                    and not parts[0].strip() == "ROOT":
                is_context = True

        if is_context:
            hist[data_type][data_class]["context"][i] = data
        else:
            hist[data_type][data_class]["no_context"][i] = data

    #print data
    for relation_type in hist.keys():
        for relation_class in sorted(hist[relation_type].keys()):
            context_class = "context"
            no_context_class = "no_context"
            context_num = len(hist[relation_type][relation_class][context_class].keys())
            no_context_num = len(hist[relation_type][relation_class][no_context_class].keys())

            percentage = 1.0
            denominator =float(no_context_num)+float(context_num)
            percentage = int(float(context_num)/denominator*100)
            print(f"--{relation_type}.{relation_class}.{context_class}: {context_num}/{denominator} == {str(percentage)}%")