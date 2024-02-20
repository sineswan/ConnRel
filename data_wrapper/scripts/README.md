
# Creating data files for data from DISRPT

```python
--disrpt_input
C:\_data\work\data\sharedtask2023-main\data
--ddtb_input
C:\_data\work\data\ddtb_data
--output
C:\_data\work\code\ConnRel\data\dataset
--home
"debugging-"
--modes="[1]"
--sizes="[1]"
--dataset="eng.dep.scidtb"

#e.g.,
#python ./data_wrapper/scripts/create_data_for_connrel.py --disrpt_input ~/work/data/sharedtask2023-main/data/ --ddtb_input ~/work/data/ddtb_data --output data/dataset --home /home/wansn/work/code/stephen-wan/ConnRel/ --jeon_discourse_segments data/dataset/jeon_segments/eng_dep_covdtb/jeon_discourse_segments.csv --jeon_sentence_segments data/dataset/jeon_segments/eng_dep_covdtb/jeon_sentence_segments.csv --jeon_docid_mapping data/dataset/jeon_segments/eng_dep_covdtb/eng_dep_covdtb.docid_mapping_jeon.json  --modes="[1]" --sizes="[2,3]"
```

# Running analysis to compare predictions

```python
--result1
C:\_data\work\code\2023-jca\projs\paper_statistics\ConnRel\data\dataset\eng_dep_scidtb\withContext\mode-1.1-context-1\eng_dep_scidtb\fine\preds\joint+test_l1+3+106524.txt
--result2
C:\_data\work\code\2023-jca\projs\paper_statistics\ConnRel\data\dataset\eng_dep_scidtb\withContext\mode-2-context-1\eng_dep_scidtb\fine\preds\joint+test_l1+3+106524.txt
```