import pathlib

import pandas as pd

import tracklab


def main():
    tracklab.init(name=pathlib.Path(__file__).stem)

    # Get a pandas DataFrame object of all the data in the csv file:
    df = pd.read_csv(pathlib.Path(__file__).parent.resolve() / "tweets.csv")

    # Get pandas Series object of the "tweet text" column:
    text = df["tweet_text"]

    # Get pandas Series object of the "emotion" column:
    target = df["is_there_an_emotion_directed_at_a_brand_or_product"]

    # Remove the blank rows from the series:
    target = target[pd.notnull(text)]
    text = text[pd.notnull(text)]

    # Perform feature extraction:
    from sklearn.feature_extraction.text import CountVectorizer

    count_vect = CountVectorizer()
    count_vect.fit(text)
    counts = count_vect.transform(text)

    # counts_train = counts[:6000]
    # target_train = target[:6000]
    counts_test = counts[6000:]
    target_test = target[6000:]

    # Train with this data with a Naive Bayes classifier:
    from sklearn.naive_bayes import MultinomialNB

    nb = MultinomialNB()
    nb.fit(counts, target)

    X_test = counts_test  # noqa: N806
    y_test = target_test
    y_probas = nb.predict_proba(X_test)
    y_pred = nb.predict(X_test)

    print("y", y_probas.shape)

    # ROC
    tracklab.log({"roc": tracklab.plot.roc_curve(y_test, y_probas, nb.classes_)})
    tracklab.log(
        {
            "roc_with_title": tracklab.plot.roc_curve(
                y_test, y_probas, nb.classes_, title="MY ROC TITLE"
            )
        }
    )

    # Precision Recall
    tracklab.log({"pr": tracklab.plot.pr_curve(y_test, y_probas, nb.classes_)})
    tracklab.log(
        {
            "pr_with_title": tracklab.plot.pr_curve(
                y_test, y_probas, nb.classes_, title="MY PR TITLE"
            )
        }
    )

    # Confusion Matrix
    class_ind_map = {}
    for i, class_name in enumerate(nb.classes_):
        class_ind_map[class_name] = i
    y_pred_inds = [class_ind_map[class_name] for class_name in y_pred]
    y_true_inds = [class_ind_map[class_name] for class_name in y_test]
    # test workflow with classes
    tracklab.log(
        {
            "conf_mat": tracklab.plot.confusion_matrix(
                preds=y_pred_inds, y_true=y_true_inds, class_names=nb.classes_
            )
        }
    )
    # test workflow without classes
    tracklab.log(
        {
            "conf_mat_noclass": tracklab.plot.confusion_matrix(
                preds=y_pred_inds, y_true=y_true_inds
            )
        }
    )
    # test workflow with multiples of inds
    y_pred_mult = [y_pred_ind * 5 for y_pred_ind in y_pred_inds]
    y_true_mult = [y_true_ind * 5 for y_true_ind in y_true_inds]
    tracklab.log(
        {
            "conf_mat_noclass_mult": tracklab.plot.confusion_matrix(
                preds=y_pred_mult, y_true=y_true_mult, title="I HAVE A TITLE"
            )
        }
    )

    # test probs workflow
    tracklab.log(
        {
            "conf_mat_probs": tracklab.plot.confusion_matrix(
                probs=y_probas, y_true=y_true_inds, class_names=nb.classes_
            )
        }
    )


if __name__ == "__main__":
    main()
