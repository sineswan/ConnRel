# Discourse connective generation and relation classification

This code base is based on https://github.com/liuwei1206/ConnRel 

## 1. Requirement
Our working environment is Python 3.8. Before you run the code, please make sure you have installed all the required packages. You can achieve it by simply execute the shell as `sh requirements.sh`

Then you need to download roberta-base from [here](https://huggingface.co/roberta-base/tree/main), and put it under the folder "data/pretrained_models/roberta-base".

## 2. Data and Preprocessing
**For PDTB 2.0**
1. copy the raw corpus (folder with .pdtb files) under the folder "data/dataset/pdtb2/raw", 
2. do preprocessing via `python3 preprocessing`. (you may need to active some codes in main function of preprocesing.py). The raw corpus looks like: 00, 01, 02, ..., 24.

```python
#Either default:
python3 preprocessing

#or with context: mode 0 (prior text, maximum), mode 1 (gold labelled linked prior text)
python preprocessing.py --pdtb2_raw_text_dir ../../../data/pdtb_v2_LDC2008T05/pdtb_v2/data/raw/wsj --context_mode 1

#to create data from DISRPT
#(see data_wrapper/readme.md)
python ./data_wrapper/scripts/create_data_for_connrel.py --disrpt_input ~/work/data/sharedtask2023-main/data/ --ddtb_input ~/work/data/ddtb_data --output data/dataset --home /home/wansn/work/code/stephen-wan/ConnRel/

#to create jeon data for DISRPT data set
#1. follow instructions in Stephen's fork of Sungho Jeon's EMNLP2020 code
2.

```

**For PDTB 3.0**
1. copy the raw corpus under the folder "data/dataset/pdtb3/raw/gold" and "data/dataset/pdtb3/raw/data", where the former is label files and the latter is text files. 
2. do preprocessing via `python3 preprocessing`. (you may need to active some codes in main function of preprocesing.py). The corpus in both raw/gold and raw/data looks like: 00, 01, 02, ..., 24.

**For PCC**
1. Download raw corpus from [here](http://angcl.ling.uni-potsdam.de/resources/pcc2.2.zip) and unzip the file. 
2. Go into the unzip directory, do `python3 connectives_xml2tsv.py`. It will generate a file called "pcc_discourse_relations_all.tsv". 
3. Put the file "pcc_discourse_relations_all.tsv" under the folder "data/dataset/pcc/raw".
4. Do preprocessing via `python3 preprocessing`. (you may need to active some codes in main function of preprocesing.py).

## 3. Run
**For PDTB 2.0**, you can directly run each script. For instance, you can do `sh run_joint.sh` to reproduce the results of our method.

**For PDTB 3.0**, you need to change (set) the dataset parameter in script to "pdtb3". Note that, in order to reproduce our results, you also need to modify the `sample_k` to 200. For more details, please refer to the paper.

**For PCC**, you need to change the dataset into "pcc" and modify the `sample_k` to 10 and `conn_threshold` to 5.

## 4. Citation
...