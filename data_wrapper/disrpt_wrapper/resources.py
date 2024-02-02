#Taken from https://raw.githubusercontent.com/merelscholman/DiscoGeM/main/Appendix/connective_exclusion_list
#Connective exclusion list: If any of these occurred within the first five words of a sentence, the sentence and its preceding sentence were not considered as implicit relation candidate.

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

scidtb_filtered_connectives = \
{
    #only place where we use "but"
   "contrast": {
      "but": 31,
      "however": 20,
      "even": 7,
      "while": 5,
      "whereas": 4,
      "rather": 4,
      "yet": 4,
      "as": 4,
      "instead": 3,
      "although": 2,
      "in": 2,
      "despite": 2,
      "contradicting": 2
   },

    # only place where we use "and"
   "joint": {
      "and": 508,
      "or": 23,
      # "(": 15,
      "while": 10,
      # "but": 7
      # "the": 6,
      # "2": 5,
      # "as": 2,
      # "fitting": 2,
      # "resolve": 2
   },
   "bg-general": {
      "based": 133,
      "according": 4,
      "given": 4,
      "via": 2,
      "even": 2
   },
   "elab-addition": {
      "that": 583,
      "which": 351,
      "for": 106,
      "in": 102,
      "to": 92,
      "of": 90,
      "where": 85,
      # "the": 57,
      # "(": 52,
      # "using": 41,
      # "used": 39,
      # "we": 32,
      # "called": 31,
      # "trained": 28,
      # "this": 23,
      # "without": 20,
      # "containing": 19,
      # "as": 18,
      # "extracted": 18,
      # "it": 16,
      # "involving": 15,
      # "including": 15,
      # "associated": 15,
      # "derived": 14,
      # "whose": 14,
      # "a": 13,
      # "obtained": 13,
      # "written": 12,
      # "mentioned": 12,
      # "with": 12,
      # "related": 11,
      # "made": 11,
      # "produced": 11,
      # "these": 10,
      # "provided": 10,
      # "given": 10,
      # "applied": 9,
      # "they": 9,
      # "not": 9,
      # "designed": 9,
      # "consisting": 9,
      # "generated": 8,
      # "required": 8,
      # "our": 7,
      # "making": 7,
      # "on": 7,
      # "found": 7,
      # "described": 7,
      # "by": 6,
      # "showing": 6,
      # "outperforming": 6,
      # "allowing": 6,
      # "learned": 6,
      # "comparing": 6,
      # "capable": 6,
      # "based": 6,
      # "captured": 6,
      # "-": 5,
      # "at": 5,
      # "when": 5,
      # "achieving": 5,
      # "taking": 5,
      # "from": 5,
      # "caused": 5,
      # "obtaining": 5,
      # "leveraging": 5,
      # "conducted": 4,
      # "expressed": 4,
      # "such": 4,
      # "reported": 4,
      # "supporting": 4,
      # "annotated": 4,
      # "all": 4,
      # "automatically": 4,
      # "combined": 4,
      # "referred": 4,
      # "achieved": 4,
      # "defined": 4,
      # "improving": 4,
      # "known": 4,
      # "built": 4,
      # "offered": 4,
      # "underlying": 4,
      # "complementing": 4,
      # "while": 4,
      # "learnt": 4,
      # "comprising": 4,
      # "each": 4,
      # "conditioned": 4,
      # "demonstrating": 3,
      # "needed": 3,
      # "coming": 3,
      # "leading": 3,
      # "typically": 3,
      # "depending": 3,
      # "followed": 3,
      # "drawn": 3,
      # "pertaining": 3,
      # "enabling": 3,
      # "requiring": 3,
      # "inspired": 3,
      # "yielding": 3,
      # "collected": 3,
      # "specially": 3,
      # "being": 3,
      # "determined": 3,
      # "corresponding": 3,
      # "representing": 3,
      # "involved": 3,
      # "estimated": 3,
      # "specialized": 3,
      # "devised": 3,
      # "assumed": 3,
      # "trying": 3,
      # "looking": 3,
      # "approaching": 3,
      # "through": 3,
      # "surrounding": 3,
      # "published": 3,
      # "incorporating": 3,
      # "specified": 3,
      # "only": 3,
      # "specifically": 3,
      # "composed": 3,
      # "giving": 3,
      # "resulting": 3,
      # "implementing": 3,
      # "an": 3,
      # "directly": 2,
      # "represented": 2,
      # "presented": 2,
      # "reducing": 2,
      # "most": 2,
      # "regarding": 2,
      # "acquired": 2,
      # "embedded": 2,
      # "encoded": 2,
      # "having": 2,
      # "focusing": 2,
      # "capturing": 2,
      # "providing": 2,
      # "adapted": 2,
      # "previous": 2,
      # "mapping": 2,
      # "describing": 2,
      # "created": 2,
      # "either": 2,
      # "explored": 2,
      # "bringing": 2,
      # "currently": 2,
      # "exhibited": 2,
      # "covering": 2,
      # "according": 2,
      # "focused": 2,
      # "whether": 2,
      # "consistent": 2,
      # "via": 2,
      # "users'": 2,
      # "does": 2,
      # "except": 2,
      # "offering": 2,
      # "however": 2,
      # "varying": 2,
      # "who": 2,
      # "dubbed": 2,
      # "explaining": 2,
      # "refined": 2,
      # "spanning": 2,
      # "guided": 2,
      # "answers": 2,
      # "covered": 2,
      # "centered": 2,
      # "crawled": 2,
      # "commonly": 2,
      # "sampled": 2,
      # "tailored": 2,
      # "especially": 2,
      # "substantially": 2,
      # "existing": 2,
      # "labeled": 2,
      # "benefiting": 2,
      # "posting": 2,
      # "joining": 2,
      # "harnessing": 2,
      # "arranged": 2,
      # "afforded": 2,
      # "born": 2,
      # "combining": 2,
      # "easily": 2,
      # "considered": 2,
      # "both": 2,
      # "situated": 2,
      # "hidden": 2,
      # "whereby": 2,
      # "raised": 2,
      # "extending": 2,
      # "disclosed": 2,
      # "stemming": 2,
      # ":": 2,
      # "how": 2
   },
   "exp-evidence": {
      # "on": 3,
      # "our": 2,
      # "(": 2,
      "outperforming": 2
   },
   "comparison": {
      "compared": 30,
      "than": 13,
      "as": 5,
      "when": 2,
      "in": 2,
      "while": 2,
      "outperforming": 2,
      "over": 2
   },
   # "ROOT": {
   #    "we": 185,
   #    "this": 87,
   #    "in": 50,
   #    "a": 4,
   #    "the": 4
   # },
   "enablement": {
      "to": 615,
      "for": 90,
      "in": 14,
      "so": 5,
      # "(": 3,
      "thereby": 2
   },
   "result": {
      "resulting": 6,
      "thus": 5,
      "and": 5,
      "so": 4,
      "achieving": 3,
      "our": 3,
      "it": 2,
      "leading": 2
   },
   "bg-compare": {
       #manual
       "previously":9999
   },
   "manner-means": {
      "by": 193,
      "using": 175,
      "via": 10,
      "based": 7,
      "we": 6,
      # "(": 5,
      "with": 5,
      "through": 4,
      # "a": 2,
      # "that": 2
   },
   "elab-example": {
      # "(": 47,
      "such": 36,
      "including": 25,
      "for": 7,
      "i.e.": 3,
      "like": 3,
      "involving": 2,
      "e.g.": 2
   },
   "progression": {
      # "and": 63,
      # "but": 10,
      "furthermore": 3,
      "then": 2,
      "moreover": 2,
      # "in": 2,
      # "we": 2
   },
   #manual, possible data error
   "elab-enumember": {
      "including": 9999,
   },
   "elab-enum_member": {
      # "(": 20,
      "including": 12,
      # "a": 10,
      # "one": 9,
      # "the": 7,
      # ":": 4,
      # "first": 4,
      # "human-computer": 3,
      # "spouse": 3,
      # "wikipedia": 3,
      # "which": 2,
      # "1": 2,
      # "cross-domain": 2,
      # "small": 2,
      # "topic": 2,
      # "negative": 2,
      # "heuristics-based": 2,
      # "noise": 2,
      # "neural": 2,
      # "bounded": 2,
      # "text": 2,
      # "telephone": 2,
      # "formula": 2,
      # "-": 2,
      # "russian": 2
   },
   "temporal": {
      "when": 45,
      "while": 23,
      "during": 7,
      "after": 2,
      "before": 2,
      "as": 2,
      "until": 2
   },
   "elab-aspect": {
      # "we": 8,
      # "the": 6,
      # "a": 5,
      "that": 4,
      # "first": 4,
      # "our": 3,
      # "in": 3,
      # "(": 2,
      # "1": 2
   },
   "elab-definition": {
      # "(": 9,
      # "a": 5,
      # "namely": 2,
      # "the": 2,
      # "that": 2,
      #manual
      "by definition":-1
      # "translating": 2
   },
   "exp-reason": {
       #manual
       "since":9999,
      "because": 16,
      "due": 12,
      # "since": 12,
      "as": 11,
      # "in": 4,
      "largely": 3,
      # "we": 2,
      "mainly": 2
   },
   "condition": {
      "when": 29,
      "without": 14,
      "given": 9,
      "if": 8,
      # "in": 4,
      "as": 3,
      "even": 3,
      "with": 3,
      "while": 3
   },
   "elab-process_step": {
      "first": 5,
      # "we": 4,
      # "and": 3,
      # "(": 2
   },
   "same-unit": {
      "closely": 2
   },
   "evaluation": {
        #manual
        "we show":-1
      # "the": 4,
      # "we": 3,
      # "to": 3,
      # "in": 2
   },
   "cause": {
       #manual
       "because":9999,
      "and": 10,
      "due": 7,
      "thus": 4,
      "caused": 4,
      # "because": 3,
      "as": 3,
      "so": 2,
      "since": 2,
      "resulting": 2,
      "hence": 2,
      # "our": 2
   },
   "attribution": {
      "that": 77,
      "how": 4,
      "which": 2
   },
   "bg-goal": {
      "based": 7
   },
   "summary": {
       #manual
       "in conclusion":9999
   }
}

covdtb_filtered_connectives = \
{
   "elaboration": {
      "that": 67,
      "the": 38,
      "which": 38,
      "in": 34,
      "such": 27,
      "and": 26,
      "to": 19,
      "including": 19,
      "of": 17,
      "who": 11,
      "we": 10,
      "as": 8,
      "associated": 8,
      "related": 7,
      "where": 6,
      "a": 6,
      "reported": 5,
      "for": 5,
      "aged": 5,
      "this": 4,
      "they": 4,
      "involved": 4,
      "regarding": 4,
      "among": 4,
      "i.e.": 4,
      "born": 4,
      "showing": 3,
      "ranging": 3,
      "obtained": 3,
      "extracted": 3,
      "clinical": 3,
      "there": 3,
      "published": 3,
      "presented": 3,
      "used": 3,
      "cleaved": 3,
      "dics": 3,
      "provided": 3,
      "interestingly": 3,
      "involving": 2,
      "with": 2,
      "how": 2,
      "furthermore": 2,
      "two": 2,
      "comparing": 2,
      "comprising": 2,
      "representing": 2,
      "called": 2,
      "affecting": 2,
      "carrying": 2,
      "at": 2,
      "occupied": 2,
      "produced": 2,
      "these": 2,
      "further": 2,
      "some": 2,
      "employed": 2,
      "corresponding": 2,
      "using": 2,
      "essential": 2,
      "containing": 2,
      "since": 2,
      "taken": 2,
      "initiated": 2,
      "encoding": 2,
      "not": 2,
      "moreover": 2,
      "respondents": 2,
      "severe": 2,
      "specifically": 2,
      "several": 2,
      "depending": 2,
      "three": 2,
      "after": 2,
      "concerning": 2,
      "hospitalized": 2,
      "named": 2,
      "immunized": 2
   },
   "enablement": {
      "to": 122,
      "for": 17,
      "that": 4,
      "which": 3,
      "in": 3,
      "aimed": 3
   },
   "manner-means": {
      "using": 33,
      "by": 15
   },
   "cause-result": {
      "due": 10,
      "which": 9,
      "and": 9,
      "because": 4,
      "resulting": 4,
      "leading": 4,
      "as": 3,
      "based": 3,
      "hence": 3,
      "caused": 2,
      "that": 2,
      "causing": 2
   },
   "condition": {
      "if": 5
   },
   "comparison": {
      "but": 25,
      "compared": 9,
      "however": 8,
      "while": 6,
      "whereas": 4,
      "although": 3,
      "in": 2,
      "the": 2
   },
   "root": {
      "in": 7,
      "this": 7,
      "the": 5,
      "we": 4
   },
   "joint": {
      "and": 113,
      "but": 3,
      "or": 3,
      "as": 2
   },
   "textual-organization": {
      #manual: following https://aclanthology.org/2022.tacl-1.8.pdf, mapping to elaboration
      "that": 9999
   },
   "findings": {
      "the": 3
   },
   "temporal": {
      "when": 2,
      "following": 2,
      "as": 2,
      "followed": 2
   },
   "background": {
      # manual, using data from scidtb
      "based": 9999,
   }
}


filtered_connectives = {
   "eng.dep.scidtb":scidtb_filtered_connectives,
   "eng.dep.covdtb":covdtb_filtered_connectives,
   "general":scidtb_filtered_connectives,
}


ddtb_dataset_file_extensions = {
   "eng.dep.scidtb":".edu.txt.dep",
   "eng.dep.covdtb":".dep",
   "eng.rst.gum": ""
}