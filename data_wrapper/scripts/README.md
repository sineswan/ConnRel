
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
```

# Running analysis to compare predictions

```python
--result1
C:\_data\work\code\2023-jca\projs\paper_statistics\ConnRel\data\dataset\eng_dep_scidtb\withContext\mode-1.1-context-1\eng_dep_scidtb\fine\preds\joint+test_l1+3+106524.txt
--result2
C:\_data\work\code\2023-jca\projs\paper_statistics\ConnRel\data\dataset\eng_dep_scidtb\withContext\mode-2-context-1\eng_dep_scidtb\fine\preds\joint+test_l1+3+106524.txt
```