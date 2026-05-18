| algorithm         | family               |   precision_macro |   recall_macro |   f1_macro |   roc_auc_attack |   train_s |   predict_us_per_sample |
|:------------------|:---------------------|------------------:|---------------:|-----------:|-----------------:|----------:|------------------------:|
| one_class_svm     | one-class-boundary   |          0.908557 |       0.905571 |   0.907043 |         0.956231 |     0.044 |                    54   |
| gradient_boosting | supervised-boosting  |          0.918646 |       0.897143 |   0.906614 |         0.997441 |    51.97  |                     6.9 |
| random_forest     | supervised-ensemble  |          0.940728 |       0.867048 |   0.876119 |         0.99821  |     0.384 |                    26   |
| isolation_forest  | unsupervised-density |          0.801314 |       0.848095 |   0.811371 |         0.952562 |     0.227 |                     8   |