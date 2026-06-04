| algorithm         | family               |   precision_macro |   recall_macro |   f1_macro |   roc_auc_attack |   train_s |   predict_us_per_sample |
|:------------------|:---------------------|------------------:|---------------:|-----------:|-----------------:|----------:|------------------------:|
| gradient_boosting | supervised-boosting  |          0.942724 |       0.941963 |   0.942069 |         0.979276 |    30.734 |                     7.4 |
| random_forest     | supervised-ensemble  |          0.942015 |       0.941398 |   0.941539 |         0.977591 |     0.415 |                    45.4 |
| isolation_forest  | unsupervised-density |          0.696496 |       0.791803 |   0.714583 |         0.849354 |     0.226 |                     8.3 |
| one_class_svm     | one-class-boundary   |          0.578047 |       0.604913 |   0.411179 |         0.505172 |     0.019 |                     4.6 |