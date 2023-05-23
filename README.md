# Annotation-Inspired Implicit Discourse Relation Classification with Auxiliary Discourse Connective Generation
Code for the ACL 2023 paper "Annotation-Inspired Implicit Discourse Relation Classification with Auxiliary Discourse Connective Generation"

If any questions, please contact the email: willie1206@163.com

## 1. Requirement
Our working environment is Python 3.8. Before you run the code, please make sure you have installed all the required packages. You can achieve it by simply execute the shell as `sh requirements.sh`

Then you need to download roberta-base from [here](https://huggingface.co/roberta-base/tree/main), and put it under the folder "data/pretrained_models/roberta-base".

## 2. Data and Preprocessing
For PDTB 2.0, copy the raw corpus under the folder "data/dataset/pdtb2/raw", and then do preprocessing via `python3 preprocessing`. (you may need to modify some easy codes in main function of preprocesing.py). The raw corpus looks like: 00, 01, 02, ..., 24.

For PDTB 3.0, copy the raw corpus under the folder "data/dataset/pdtb3/raw/gold" and "data/dataset/pdtb3/raw/data", where the former is label files and the latter is text files. Then, do preprocessing via `python3 preprocessing`. (you may need to modify some easy codes in main function of preprocesing.py). The corpus in both raw/gold and raw/data looks like: 00, 01, 02, ..., 24.

## 3. Run
For PDTB 2.0, you can directly run each script. For instance, you can do `sh run_joint.sh` to reproduce the results of our method.

For PDTB 3.0, you need to change (set) the dataset parameter in script to "pdtb3". Note that, in order to reproduce our results, you also need to modify the `sample_k` to 200. For more details, please refer to the paper.

## 4. Citation
You can cite our paper through:
