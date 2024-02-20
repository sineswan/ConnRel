import argparse
import csv

from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

discoGEM_explicit_connectives = [
"accordingly",
"additionally",
"admittedly",
"after all",
"afterwards",
"also",
"alternatively",
"and",
"as a result",
"as an alternative",
"at one point",
"at the same time",
"at the time",
"because",
"besides",
"but",
"by comparison",
"by contrast",
"by then",
"consequently",
"despite that",
"despite this",
"essentially",
"even so",
"except that",
"finally",
"first",
"firstly",
"for example",
"for instance",
"for that reason",
"for this reason",
"fourth",
"furthermore",
"hence",
"however",
"in addition",
"in any case",
"in brief",
"in conclusion",
"in contrast",
"in fact",
"in other words",
"in particular",
"in short",
"in spite of that",
"in spite of this",
"in sum",
"in the end",
"in the meantime",
"in the meanwhile",
"in the same way",
"in this vein",
"in this way",
"incidentally",
"indeed",
"initially",
"initially",
"instead",
"meanwhile",
"more accurately",
"moreover",
"nevertheless",
"next",
"nonetheless",
"nor",
"on the contrary",
"on the one hand",
"on the other hand",
"one of the reasons",
"or",
"otherwise",
"particularly",
"previously",
"quite the contrary",
"quite the opposite",
"result of this",
"second",
"secondly",
"separately",
"similar",
"simultaneously",
"so",
"specifically",
"still",
"subsequently",
"that being the case",
"that is why",
"that means",
"then",
"thereby",
"therefore",
"third",
"thirdly",
"this being the case",
"this clearly shows that",
"this explains",
"this has resulted",
"this is because",
"this is why",
"this means",
"this shows that",
"though",
"though",
"thus",
"to start with",
"ultimately",
"well",
"what is more",
"with this in mind",
"yet"
]

pdtb_implicit_connectives = ['however', 'and', 'for example', 'although', 'in short', 'rather', 'specifically', 'then', 'also',
             'in particular', 'because', 'for instance', 'as a result', 'while', 'consequently', 'in other words',
             'thus', 'furthermore', 'but', 'therefore', 'so', 'in addition', 'indeed', 'since', 'in fact', 'previously',
             'instead', 'by comparison', 'as', 'that is', 'by contrast', 'meanwhile', '<unk>']

pdtb3_connectives = [
"and",
"but",
"also",
"if",
"when",
"while",
"because",
"as",
"after",
"however",
"by",
"or",
"although",
"then",
"with",
"before",
"so",
"though",
"since",
"for example",
"meanwhile",
"still",
"until",
"in addition",
"instead",
"yet",
"unless",
"thus",
"indeed",
"moreover",
"without",
"even though",
"later",
"for instance",
"even if",
"once",
"in fact",
"as a result",
"separately",
"in",
"at the same time",
"for",
"in order",
"previously",
"instead of",
"if then",
"rather than",
"either or",
"finally",
"on the other hand",
"nevertheless",
"by contrast",
"nor",
"nonetheless",
"so that",
"as long as",
"now that",
"therefore",
"as soon as",
"ultimately",
"not only but",
"in other words",
"as well",
"as if",
"otherwise",
"besides",
"rather",
"in the meantime",
"in particular",
"similarly",
"even when",
"only if",
"thereafter",
"except",
"in the end",
"even before",
"furthermore",
"thereby",
"earlier",
"in contrast",
"even as",
"consequently",
"not only but also",
"by comparison",
"because of",
"even so",
"likewise",
"specifically",
"despite",
"given",
"regardless of",
"additionally",
"as well as",
"no matter",
"both and",
"if only",
"by then",
"alternatively",
"afterward",
"whenever",
"whether",
"further",
"from",
"upon",
"only",
"so long as",
"as much as",
"even after",
"as though",
"not only",
"in short",
"in case",
"simultaneously",
"afterwards",
"like",
"next",
"in any case",
"neither nor",
"even while",
"that is",
"subsequently",
"whatever",
"whereas",
"hence",
"as an alternative",
"on the contrary",
"or otherwise",
"depending on",
"insofar as",
"much less",
"even then",
"but then",
"later on",
"such as",
"in sum",
"so as",
"accordingly",
"regardless",
"conversely",
"beyond",
"lest",
"till",
"on the one hand on the other",
"not only because of",
"not just but also",
"not so much as",
"before and after",
"in the meanwhile",
"even before then",
"but then again",
"not just but",
"when and if",
"if and when",
"so much as",
"more accurately",
"since before",
"along with",
"even with",
"and then",
"due to",
"meantime",
"albeit",
"and/or",
"where",
"about",
"plus",
"else",
"on"
]
pdtb2_connectives = ["but",
"and",
"also",
"if",
"when",
"because",
"while",
"as",
"after",
"however",
"although",
"though",
"then",
"before",
"so",
"since",
"for example",
"meanwhile",
"still",
"until",
"in addition",
"instead",
"yet",
"thus",
"indeed",
"unless",
"moreover",
"later",
"for instance",
"once",
"or",
"in fact",
"as a result",
"separately",
"previously",
"if then",
"finally",
"on the other hand",
"in turn",
"nevertheless",
"by contrast",
"nor",
"nonetheless",
"so that",
"as long as",
"otherwise",
"now that",
"therefore",
"as soon as",
"ultimately",
"in other words",
"as if",
"besides",
"rather",
"in particular",
"similarly",
"meantime",
"thereafter",
"thereby",
"earlier",
"in the end",
"in contrast",
"consequently",
"furthermore",
"afterward",
"overall",
"except",
"by comparison",
"likewise",
"specifically",
"as well",
"additionally",
"further",
"much as",
"by then",
"alternatively",
"next",
"as though",
"in short",
"simultaneously",
"neither nor",
"whereas",
"for",
"as an alternative",
"on the contrary",
"either or",
"in sum",
"accordingly",
"regardless",
"conversely",
"hence",
"lest",
"before and after",
"when and if",
"if and when",
"insofar as",
"plus",
"else"
  ]


resource_connectives = list(set(discoGEM_explicit_connectives).intersection(set(pdtb_implicit_connectives).intersection(set(pdtb3_connectives).intersection(set(pdtb2_connectives)))))

def read_file(filename):
    data = []
    with open(filename, encoding="utf-8") as f:
    #     for i,line in enumerate(f.readlines()):
    #         if i==0:
    #             pass    #skip header line
    #         else:
    #             datum = {
    #                 "gold_conn" : line[:20],
    #                 "pred_conn" : line[21:40],
    #                 "gold_label" : line[41:60],
    #                 "pred_label" : line[61:80],
    #                 "text" : line[81:]
    #             }
    #             data.append(datum)

        csv_reader = csv.DictReader(f.readlines(), delimiter="\t", quoting=csv.QUOTE_ALL)
        for row in csv_reader:
            data.append(row)

    cleaned_data = []
    for datum in data:
        clean_datum = {}
        for key in datum.keys():
            if not key=="Text":
                # print(f"key: {key}, datum: {datum}")
                value = datum[key]
                if not value:
                    value = ""
                clean_datum[key.strip()] = value.strip()
            else:
                clean_datum[key.strip()] = datum[key]
        cleaned_data.append(clean_datum)
    # print(f"Data: {json.dumps(cleaned_data, indent=3)}")
    return cleaned_data

def analyse_error_rates(data):
    stats = {}
    for datum in data:
        if not datum["Label"] in stats.keys():
            stats[datum["Label"]] = []
        result = 0
        if (datum["Label"]==datum["Pred"]):
            result =1
        stats[datum["Label"]].append(result)

    # for label in stats.keys():
    #     print(f"label: {label}: pos: {sum(stats[label])}, tot: {len(stats[label])}")

    return stats

def compare_stats(data1, data2):
    diffs = {}
    for key in data1.keys():
        if key in data2.keys():
            val1 = data1[key]
            val2 = data2[key]
            diff = sum(val1)-sum(val2)
            scale = 1/len(data1[key])
            diffs[key] = diff #c*scale

    #sort the diffs
    sorted_diffs = {k: v for k, v in sorted(diffs.items(), key=lambda item: item[1])}
    for key in sorted_diffs:

        print(f"{key}: {sorted_diffs[key]}, {sorted_diffs[key]/len(data1[key])} % #: {len(data1[key])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--result1", required=True, help="Baseline classification predictions file")
    parser.add_argument("--result2", required=True, help="System classification predictions file")
    args = parser.parse_args()

    print(f"Generating plots for class-based analysis")
    print(f"Data1")
    data1 = read_file(args.result1)
    stats1 = analyse_error_rates(data1)

    print(f"\nData2")
    data2 = read_file(args.result2)
    stats2 = analyse_error_rates(data2)

    print(f"\nComparisons")
    compare_stats(stats1, stats2)

    # print(f"\nConfusion Matrix: Data1")
    # y_true = [datum["Label"] for datum in data1]
    # y_pred =  [datum["Pred"] for datum in data1]
    # print( confusion_matrix(y_true, y_pred, labels=list(set(y_true))))

    print(f"\nConfusion Matrix: Data2")
    y_true = [datum["Label"] for datum in data2]
    y_pred =  [datum["Pred"] for datum in data2]
    labels =list(set(y_true))
    # cm = confusion_matrix(y_true, y_pred, labels=labels)

    disp = ConfusionMatrixDisplay.from_predictions(y_true, y_pred, labels=labels, xticks_rotation="vertical")
    disp.plot()
    plt.show()