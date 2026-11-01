
"""Train and compare Olist satisfaction, late-delivery and delivery-time models.

Main model:
- Predicts not_satisfied (review score 1-3).
- Uses order-time features only.
- Compares Logistic Regression, Random Forest and Extra Trees.
- Selects the model using training-only cross-validation.
- Evaluates the selected model on an untouched stratified test set.

The saved model bundle remains compatible with src.predict.
"""

from __future__ import annotations

import json
import warnings

import joblib
import numpy as np
import pandas as pd

from scipy import stats as scipy_stats
from scipy.stats import chi2_contingency

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    roc_auc_score,
    r2_score,
)
from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    cross_validate,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src import config, data_loader, features

warnings.filterwarnings("ignore", category=FutureWarning)


# ---------------------------------------------------------
# 1. GENERAL HELPERS
# ---------------------------------------------------------

def _column(df: pd.DataFrame, names: list[str]) -> str | None:
    lookup = {str(c).strip().lower(): c for c in df.columns}
    return next(
        (lookup[n.lower()] for n in names if n.lower() in lookup),
        None
    )


def _preprocessor(X: pd.DataFrame) -> ColumnTransformer:

    numeric = [
        c for c in X.columns
        if c in features.NUMERIC_FEATURES
    ]

    categorical = [
        c for c in X.columns
        if c in features.CATEGORICAL_FEATURES
    ]

    transformers = []

    if numeric:
        transformers.append((
            "numeric",
            Pipeline([
                (
                    "imputer",
                    SimpleImputer(
                        strategy="median",
                        keep_empty_features=True
                    )
                ),
                ("scaler", StandardScaler()),
            ]),
            numeric
        ))

    if categorical:
        transformers.append((
            "categorical",
            Pipeline([
                (
                    "imputer",
                    SimpleImputer(strategy="most_frequent")
                ),
                (
                    "encoder",
                    OneHotEncoder(handle_unknown="ignore")
                ),
            ]),
            categorical
        ))

    if not transformers:
        raise ValueError("No usable model features are available.")

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop"
    )


def _prepare_X(frame: pd.DataFrame) -> pd.DataFrame:

    X = frame[features.FEATURE_COLUMNS].copy()

    for col in features.NUMERIC_FEATURES:
        X[col] = pd.to_numeric(
            X[col], errors="coerce"
        ).replace([np.inf, -np.inf], np.nan)

    for col in features.CATEGORICAL_FEATURES:
        X[col] = (
            X[col]
            .astype("string")
            .fillna("Unknown")
            .replace({"<NA>": "Unknown"})
        )

    return X


# ---------------------------------------------------------
# 2. BUILD MODELLING DATA
# ---------------------------------------------------------

def _load_frame() -> pd.DataFrame:

    data = data_loader.load_all()

    required = {
        "order_360",
        "items",
        "products",
        "seller_360"
    }

    missing = required - set(data)

    if missing:
        raise KeyError(
            f"Missing modelling tables: {sorted(missing)}"
        )

    order_source = data["order_360"].copy()

    order_col = _column(order_source, ["order_id"])

    if not order_col:
        raise KeyError("order_360 must contain order_id.")

    if order_col != "order_id":
        order_source = order_source.rename(
            columns={order_col: "order_id"}
        )

    score_col = _column(
        order_source,
        [
            "review_score",
            "average_review_score",
            "avg_review_score"
        ]
    )

    if not score_col:
        raise KeyError(
            "order_360 must contain order-level review_score."
        )

    if score_col != "review_score":
        order_source = order_source.rename(
            columns={score_col: "review_score"}
        )

    status_col = _column(
        order_source,
        ["order_status", "status"]
    )

    status = (
        order_source[status_col]
        .astype("string")
        .str.lower()
        if status_col
        else pd.Series(
            "unknown",
            index=order_source.index
        )
    )

    delivered_col = _column(
        order_source,
        [
            "delivered_dt",
            "order_delivered_customer_date"
        ]
    )

    estimated_col = _column(
        order_source,
        [
            "estimated_dt",
            "order_estimated_delivery_date"
        ]
    )

    purchase_col = _column(
        order_source,
        [
            "purchase_dt",
            "order_purchase_timestamp"
        ]
    )

    delivered_dt = (
        pd.to_datetime(
            order_source[delivered_col],
            errors="coerce",
            utc=True
        ).dt.tz_convert(None)
        if delivered_col
        else pd.Series(
            pd.NaT,
            index=order_source.index
        )
    )

    estimated_dt = (
        pd.to_datetime(
            order_source[estimated_col],
            errors="coerce",
            utc=True
        ).dt.tz_convert(None)
        if estimated_col
        else pd.Series(
            pd.NaT,
            index=order_source.index
        )
    )

    purchase_dt = (
        pd.to_datetime(
            order_source[purchase_col],
            errors="coerce",
            utc=True
        ).dt.tz_convert(None)
        if purchase_col
        else pd.Series(
            pd.NaT,
            index=order_source.index
        )
    )

    delivered = status.eq("delivered") | delivered_dt.notna()

    late_col = _column(order_source, ["is_late"])

    late_target = (
        pd.to_numeric(
            order_source[late_col],
            errors="coerce"
        )
        if late_col
        else pd.Series(
            np.nan,
            index=order_source.index
        )
    )

    known_dates = (
        delivered_dt.notna()
        & estimated_dt.notna()
    )

    derived_late = pd.Series(
        np.nan,
        index=order_source.index,
        dtype="float64"
    )

    derived_late.loc[known_dates] = (
        delivered_dt.loc[known_dates]
        > estimated_dt.loc[known_dates]
    ).astype(int)

    late_target = late_target.where(
        late_target.isin([0, 1]),
        derived_late
    )

    late_target = late_target.where(
        delivered,
        np.nan
    )

    duration_col = _column(
        order_source,
        ["delivery_days"]
    )

    duration_target = (
        pd.to_numeric(
            order_source[duration_col],
            errors="coerce"
        )
        if duration_col
        else pd.Series(
            np.nan,
            index=order_source.index
        )
    )

    derived_days = (
        delivered_dt - purchase_dt
    ).dt.total_seconds() / 86400

    use_dates = (
        delivered_dt.notna()
        & purchase_dt.notna()
    )

    duration_target = duration_target.where(
        ~use_dates,
        derived_days
    )

    duration_target = duration_target.where(
        delivered,
        np.nan
    )

    target_fields = pd.DataFrame({
        "order_id": order_source["order_id"],
        "late_target": late_target,
        "delivery_days_target": duration_target
    }).drop_duplicates(
        "order_id",
        keep="first"
    )

    frame = features.build_model_frame(
        order_source,
        data["items"],
        data["products"],
        data["seller_360"]
    )

    frame = frame.merge(
        target_fields,
        on="order_id",
        how="left",
        validate="one_to_one"
    )

    if frame.empty:
        raise ValueError(
            "No order-level modelling rows were generated."
        )

    frame["review_score"] = pd.to_numeric(
        frame["review_score"],
        errors="coerce"
    )

    frame.loc[
        ~frame["review_score"].between(1, 5),
        "review_score"
    ] = np.nan

    frame["late_target"] = pd.to_numeric(
        frame["late_target"],
        errors="coerce"
    )

    frame.loc[
        ~frame["late_target"].isin([0, 1]),
        "late_target"
    ] = np.nan

    frame["delivery_days_target"] = pd.to_numeric(
        frame["delivery_days_target"],
        errors="coerce"
    )

    frame.loc[
        frame["delivery_days_target"] < 0,
        "delivery_days_target"
    ] = np.nan

    return frame


# ---------------------------------------------------------
# 3. FEATURE SCREENING
# ---------------------------------------------------------

def _screen_features(
    X_train: pd.DataFrame,
    y_train: pd.Series
):

    rows = []

    for col in features.NUMERIC_FEATURES:

        if col not in X_train.columns:
            continue

        series = pd.to_numeric(
            X_train[col],
            errors="coerce"
        )

        a = series[y_train == 0].dropna()
        b = series[y_train == 1].dropna()

        statistic, pvalue = (
            scipy_stats.f_oneway(a, b)
            if len(a) > 1 and len(b) > 1
            else (np.nan, np.nan)
        )

        corr = (
            series.corr(
                y_train.astype(float),
                method="spearman"
            )
            if series.notna().sum() > 2
            and series.nunique(dropna=True) > 1
            else np.nan
        )

        rows.append({
            "feature": col,
            "feature_type": "numeric",
            "test": "ANOVA",
            "statistic": statistic,
            "p_value": pvalue,
            "spearman_target_correlation": corr
        })

    for col in features.CATEGORICAL_FEATURES:

        if col not in X_train.columns:
            continue

        temp = pd.DataFrame({
            "group": X_train[col]
            .astype("string")
            .fillna("Unknown"),
            "target": y_train
        })

        counts = temp["group"].value_counts()

        temp.loc[
            ~temp["group"].isin(
                counts[counts >= 20].index
            ),
            "group"
        ] = "Other/rare"

        table = pd.crosstab(
            temp["group"],
            temp["target"]
        )

        try:
            stat, pval, _, _ = (
                chi2_contingency(table)
                if table.shape[0] >= 2
                and table.shape[1] >= 2
                else (np.nan, np.nan, None, None)
            )
        except ValueError:
            stat, pval = np.nan, np.nan

        rows.append({
            "feature": col,
            "feature_type": "categorical",
            "test": "Chi-square",
            "statistic": stat,
            "p_value": pval,
            "spearman_target_correlation": np.nan
        })

    screening = pd.DataFrame(rows)

    if not screening.empty:
        screening = screening.sort_values(
            "p_value",
            na_position="last"
        )

    nums = [
        c for c in features.NUMERIC_FEATURES
        if c in X_train.columns
    ]

    numeric = (
        X_train[nums]
        .apply(pd.to_numeric, errors="coerce")
        if nums
        else pd.DataFrame(index=X_train.index)
    )

    if not numeric.empty:

        numeric = (
            numeric
            .replace([np.inf, -np.inf], np.nan)
            .fillna(numeric.median())
            .fillna(0)
        )

        numeric = numeric.loc[
            :,
            numeric.nunique(dropna=False) > 1
        ]

        corr = (
            numeric.corr()
            .stack()
            .rename("correlation")
            .reset_index()
        )

        corr.columns = [
            "feature_1",
            "feature_2",
            "correlation"
        ]

        corr = corr[
            corr["feature_1"] < corr["feature_2"]
        ].copy()

        corr["absolute_correlation"] = (
            corr["correlation"].abs()
        )

        corr = corr.sort_values(
            "absolute_correlation",
            ascending=False
        )

        sample = (
            numeric.sample(
                n=min(10000, len(numeric)),
                random_state=config.RANDOM_STATE
            )
            if len(numeric) > 10000
            else numeric
        )

        matrix = sample.to_numpy(dtype=float)

        z = (
            matrix - matrix.mean(axis=0)
        ) / np.where(
            matrix.std(axis=0) == 0,
            1,
            matrix.std(axis=0)
        )

        vif_rows = []

        for i, col in enumerate(numeric.columns):

            target = z[:, i]
            other = np.delete(z, i, axis=1)

            if other.shape[1] == 0:
                vif = 1.0

            else:
                design = np.column_stack([
                    np.ones(len(other)),
                    other
                ])

                beta = np.linalg.lstsq(
                    design,
                    target,
                    rcond=None
                )[0]

                fitted = design @ beta

                denominator = np.sum(
                    (target - target.mean()) ** 2
                )

                r2 = (
                    1 - np.sum(
                        (target - fitted) ** 2
                    ) / denominator
                    if denominator > 0
                    else 0.0
                )

                vif = 1 / max(
                    1 - min(max(float(r2), 0), 0.999999),
                    1e-6
                )

            vif_rows.append({
                "feature": col,
                "vif": float(vif)
            })

        vif_df = pd.DataFrame(vif_rows)

    else:

        corr = pd.DataFrame(
            columns=[
                "feature_1",
                "feature_2",
                "correlation",
                "absolute_correlation"
            ]
        )

        vif_df = pd.DataFrame(
            columns=["feature", "vif"]
        )

    return screening, corr, vif_df


# ---------------------------------------------------------
# 4. MODEL COMPARISON
# ---------------------------------------------------------

def _select_best_classifier(
    X_train: pd.DataFrame,
    y_train: pd.Series
):

    counts = y_train.value_counts()

    folds = min(
        config.N_CV_FOLDS,
        int(counts.min())
    )

    if folds < 2:
        raise ValueError(
            "Insufficient observations for cross-validation."
        )

    cv = StratifiedKFold(
        n_splits=folds,
        shuffle=True,
        random_state=config.RANDOM_STATE
    )

    candidates = {

        "Logistic Regression": LogisticRegression(
            max_iter=2000,
            class_weight=None,
            random_state=config.RANDOM_STATE
        ),

        "Balanced Logistic Regression": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=config.RANDOM_STATE
        ),

        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            min_samples_leaf=4,
            max_features="sqrt",
            class_weight=None,
            n_jobs=-1,
            random_state=config.RANDOM_STATE
        ),

        "Extra Trees": ExtraTreesClassifier(
            n_estimators=250,
            min_samples_leaf=3,
            max_features="sqrt",
            class_weight=None,
            n_jobs=-1,
            random_state=config.RANDOM_STATE
        )
    }

    scoring = {
        "accuracy": "accuracy",
        "balanced_accuracy": "balanced_accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
        "roc_auc": "roc_auc"
    }

    results = []
    fitted_candidates = {}

    print("\nComparing classification algorithms...")

    for name, estimator in candidates.items():

        pipeline = Pipeline([
            ("preprocessor", _preprocessor(X_train)),
            ("classifier", estimator)
        ])

        scores = cross_validate(
            pipeline,
            X_train,
            y_train,
            cv=cv,
            scoring=scoring,
            n_jobs=1,
            error_score="raise"
        )

        results.append({
            "model": name,
            "cv_accuracy_mean": float(
                scores["test_accuracy"].mean()
            ),
            "cv_accuracy_std": float(
                scores["test_accuracy"].std()
            ),
            "cv_balanced_accuracy": float(
                scores["test_balanced_accuracy"].mean()
            ),
            "cv_precision": float(
                scores["test_precision"].mean()
            ),
            "cv_recall": float(
                scores["test_recall"].mean()
            ),
            "cv_f1": float(
                scores["test_f1"].mean()
            ),
            "cv_auc": float(
                scores["test_roc_auc"].mean()
            )
        })

        fitted_candidates[name] = scores

        print(
            f"{name}: "
            f"{scores['test_accuracy'].mean() * 100:.2f}% "
            f"CV accuracy"
        )

    results.sort(
        key=lambda x: (
            x["cv_accuracy_mean"],
            x["cv_auc"]
        ),
        reverse=True
    )

    best_name = results[0]["model"]
    best_estimator = candidates[best_name]

    best_pipeline = Pipeline([
        ("preprocessor", _preprocessor(X_train)),
        ("classifier", best_estimator)
    ])

    best_pipeline.fit(X_train, y_train)

    best_scores = fitted_candidates[best_name]

    return (
        best_pipeline,
        best_name,
        results,
        best_scores["test_roc_auc"],
        best_scores["test_accuracy"]
    )


# ---------------------------------------------------------
# 5. ODDS RATIOS
# ---------------------------------------------------------

def build_odds_ratios(
    model,
    positive_label="Higher odds of not satisfied",
    negative_label="Lower odds of not satisfied"
):

    if not isinstance(
        model.named_steps["classifier"],
        LogisticRegression
    ):
        return pd.DataFrame(
            columns=[
                "feature",
                "coefficient",
                "odds_ratio",
                "abs_coefficient",
                "direction"
            ]
        )

    pre = model.named_steps["preprocessor"]

    coef = model.named_steps["classifier"].coef_[0]

    names = pre.get_feature_names_out()

    output = pd.DataFrame({
        "feature": names,
        "coefficient": coef
    })

    output["odds_ratio"] = np.exp(
        np.clip(output["coefficient"], -20, 20)
    )

    output["abs_coefficient"] = (
        output["coefficient"].abs()
    )

    output["direction"] = np.where(
        output["coefficient"] > 0,
        positive_label,
        negative_label
    )

    return output.sort_values(
        "abs_coefficient",
        ascending=False
    ).reset_index(drop=True)


# ---------------------------------------------------------
# 6. CLASSIFICATION METRICS
# ---------------------------------------------------------

def _classification_metrics(
    model,
    X_test,
    y_test,
    cv_scores=None,
    target="binary target"
):

    predictions = model.predict(X_test)

    classes = list(model.classes_)

    probabilities = model.predict_proba(X_test)[
        :, classes.index(1)
    ]

    class_names = (
        ["on_time", "late"]
        if target.lower().startswith("late")
        else ["satisfied", "not_satisfied"]
    )

    return {
        "target": target,
        "n_test_rows": int(len(y_test)),
        "accuracy": float(
            accuracy_score(y_test, predictions)
        ),
        "balanced_accuracy": float(
            balanced_accuracy_score(y_test, predictions)
        ),
        "precision": float(
            precision_score(
                y_test,
                predictions,
                zero_division=0
            )
        ),
        "recall": float(
            recall_score(
                y_test,
                predictions,
                zero_division=0
            )
        ),
        "f1": float(
            f1_score(
                y_test,
                predictions,
                zero_division=0
            )
        ),
        "roc_auc": float(
            roc_auc_score(y_test, probabilities)
        ),
        "cv_auc_mean": (
            float(np.mean(cv_scores))
            if cv_scores is not None
            else None
        ),
        "confusion_matrix": confusion_matrix(
            y_test,
            predictions,
            labels=[0, 1]
        ).tolist(),
        "classification_report": classification_report(
            y_test,
            predictions,
            labels=[0, 1],
            target_names=class_names,
            output_dict=True,
            zero_division=0
        )
    }


# ---------------------------------------------------------
# 7. MAIN TRAINING FUNCTION
# ---------------------------------------------------------

def train():

    full_frame = _load_frame()

    frame = full_frame.dropna(
        subset=["review_score"]
    ).copy()

    if frame.empty:
        raise ValueError(
            "No valid review scores available."
        )

    frame["not_satisfied"] = (
        frame["review_score"]
        <= config.LOW_REVIEW_MAX_SCORE
    ).astype(int)

    X = _prepare_X(frame)

    y = frame["not_satisfied"].astype(int)

    y_score = frame["review_score"].astype(float)

    counts = y.value_counts()

    if len(counts) != 2 or int(counts.min()) < 5:
        raise ValueError(
            f"Need at least 5 rows in each class: {counts.to_dict()}"
        )

    # Fixed stratified holdout.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config.TEST_SIZE,
        random_state=config.RANDOM_STATE,
        stratify=y
    )

    yscore_train = y_score.loc[X_train.index]
    yscore_test = y_score.loc[X_test.index]

    # Compare algorithms and select using training data only.
    (
        classifier,
        selected_model,
        model_comparison,
        cv_auc_scores,
        cv_accuracy_scores
    ) = _select_best_classifier(
        X_train,
        y_train
    )

    # Final holdout predictions.
    pred = classifier.predict(X_test)

    prob = classifier.predict_proba(X_test)[
        :, list(classifier.classes_).index(1)
    ]

    # Majority-class baseline.
    dummy = Pipeline([
        ("preprocessor", _preprocessor(X_train)),
        ("classifier", DummyClassifier(strategy="prior"))
    ])

    dummy.fit(X_train, y_train)

    dummy_pred = dummy.predict(X_test)

    dummy_prob = dummy.predict_proba(X_test)[
        :, list(dummy.classes_).index(1)
    ]

    # Linear regression for numerical review score.
    regressor = Pipeline([
        ("preprocessor", _preprocessor(X_train)),
        ("regressor", LinearRegression())
    ])

    regressor.fit(X_train, yscore_train)

    score_pred = regressor.predict(X_test)

    # Feature diagnostics use training data only.
    screening, corr_df, vif_df = _screen_features(
        X_train,
        y_train
    )

    main_metrics = {
        "target": (
            "not_satisfied = 1 when review_score <= 3; "
            "satisfied = 0 when review_score is 4-5"
        ),

        "positive_class": "not satisfied (score 1-3)",

        "selected_model": selected_model,

        "n_rows": int(len(frame)),

        "n_features": int(X.shape[1]),

        "class_counts": {
            str(int(k)): int(v)
            for k, v in counts.items()
        },

        "accuracy": float(
            accuracy_score(y_test, pred)
        ),

        "balanced_accuracy": float(
            balanced_accuracy_score(y_test, pred)
        ),

        "precision": float(
            precision_score(
                y_test,
                pred,
                zero_division=0
            )
        ),

        "recall": float(
            recall_score(
                y_test,
                pred,
                zero_division=0
            )
        ),

        "f1": float(
            f1_score(
                y_test,
                pred,
                zero_division=0
            )
        ),

        "roc_auc": float(
            roc_auc_score(y_test, prob)
        ),

        "cv_accuracy_mean": float(
            np.mean(cv_accuracy_scores)
        ),

        "cv_accuracy_std": float(
            np.std(cv_accuracy_scores, ddof=1)
        ) if len(cv_accuracy_scores) > 1 else 0.0,

        "cv_auc_mean": float(
            np.mean(cv_auc_scores)
        ),

        "cv_auc_std": float(
            np.std(cv_auc_scores, ddof=1)
        ) if len(cv_auc_scores) > 1 else 0.0,

        "model_comparison": model_comparison,

        "confusion_matrix": confusion_matrix(
            y_test,
            pred,
            labels=[0, 1]
        ).tolist(),

        "classification_report": classification_report(
            y_test,
            pred,
            labels=[0, 1],
            target_names=[
                "satisfied",
                "not_satisfied"
            ],
            output_dict=True,
            zero_division=0
        ),

        "dummy_baseline": {
            "accuracy": float(
                accuracy_score(y_test, dummy_pred)
            ),
            "roc_auc": float(
                roc_auc_score(y_test, dummy_prob)
            )
        },

        "linear_baseline": {
            "rmse": float(
                np.sqrt(
                    mean_squared_error(
                        yscore_test,
                        score_pred
                    )
                )
            ),
            "mae": float(
                mean_absolute_error(
                    yscore_test,
                    score_pred
                )
            ),
            "r2": float(
                r2_score(
                    yscore_test,
                    score_pred
                )
            )
        },

        "split": "80/20 stratified train/test split",

        "cv_folds": int(
            min(
                config.N_CV_FOLDS,
                int(y_train.value_counts().min())
            )
        ),

        "feature_timing": (
            "Order-time features only. Excludes actual delivery "
            "outcomes, order status, review text, review timestamps "
            "and target review score."
        ),

        "feature_selection": {
            "method": (
                "ANOVA and chi-square screening, numeric "
                "correlation and VIF diagnostics."
            ),
            "high_numeric_correlations_ge_0_80": int(
                (
                    corr_df["absolute_correlation"] >= 0.80
                ).sum()
            ) if not corr_df.empty else 0,
            "numeric_features_vif_ge_5": int(
                (vif_df["vif"] >= 5).sum()
            ) if not vif_df.empty else 0
        }
    }

    # -----------------------------------------------------
    # 8. SUPPORTING MODEL: LATE DELIVERY
    # -----------------------------------------------------

    late_frame = full_frame.dropna(
        subset=["late_target"]
    ).copy()

    late_classifier = None

    late_odds = pd.DataFrame(
        columns=[
            "feature",
            "coefficient",
            "odds_ratio",
            "direction"
        ]
    )

    late_metrics = {
        "available": False,
        "reason": "Not enough delivered orders with known late status."
    }

    if not late_frame.empty:

        late_frame = late_frame[
            late_frame["late_target"].isin([0, 1])
        ].copy()

        late_y = late_frame["late_target"].astype(int)

        late_counts = late_y.value_counts()

        if (
            len(late_counts) == 2
            and int(late_counts.min()) >= 5
        ):

            late_X = _prepare_X(late_frame)

            LX_train, LX_test, ly_train, ly_test = train_test_split(
                late_X,
                late_y,
                test_size=config.TEST_SIZE,
                random_state=config.RANDOM_STATE,
                stratify=late_y
            )

            late_classifier = Pipeline([
                ("preprocessor", _preprocessor(LX_train)),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=1500,
                        class_weight="balanced",
                        random_state=config.RANDOM_STATE
                    )
                )
            ])

            late_classifier.fit(LX_train, ly_train)

            late_cv = StratifiedKFold(
                n_splits=min(
                    config.N_CV_FOLDS,
                    int(ly_train.value_counts().min())
                ),
                shuffle=True,
                random_state=config.RANDOM_STATE
            )

            late_auc = cross_validate(
                late_classifier,
                LX_train,
                ly_train,
                cv=late_cv,
                scoring="roc_auc",
                n_jobs=1
            )["test_score"]

            late_metrics = _classification_metrics(
                late_classifier,
                LX_test,
                ly_test,
                late_auc,
                target="late = delivered after estimated date"
            )

            late_metrics["available"] = True

            late_metrics["n_rows"] = int(
                len(late_frame)
            )

            late_metrics["class_counts"] = {
                str(int(k)): int(v)
                for k, v in late_counts.items()
            }

            late_metrics["feature_timing"] = (
                "Order-time predictors only; actual delivery "
                "and estimated dates are target labels."
            )

            late_odds = build_odds_ratios(
                late_classifier,
                positive_label="Higher odds of late delivery",
                negative_label="Lower odds of late delivery"
            )

    # -----------------------------------------------------
    # 9. SUPPORTING MODEL: DELIVERY DURATION
    # -----------------------------------------------------

    duration_frame = full_frame.dropna(
        subset=["delivery_days_target"]
    ).copy()

    delivery_regressor = None

    delivery_metrics = {
        "available": False,
        "reason": (
            "Not enough delivered orders with known "
            "purchase and delivery timestamps."
        )
    }

    if len(duration_frame) >= 30:

        duration_y = pd.to_numeric(
            duration_frame["delivery_days_target"],
            errors="coerce"
        )

        duration_ok = (
            duration_y.notna()
            & duration_y.ge(0)
        )

        duration_frame = duration_frame.loc[
            duration_ok
        ].copy()

        duration_y = duration_y.loc[
            duration_ok
        ].astype(float)

        if (
            len(duration_frame) >= 30
            and duration_y.nunique() > 1
        ):

            duration_X = _prepare_X(duration_frame)

            DX_train, DX_test, dy_train, dy_test = train_test_split(
                duration_X,
                duration_y,
                test_size=config.TEST_SIZE,
                random_state=config.RANDOM_STATE
            )

            delivery_regressor = Pipeline([
                ("preprocessor", _preprocessor(DX_train)),
                ("regressor", LinearRegression())
            ])

            delivery_regressor.fit(
                DX_train,
                dy_train
            )

            duration_pred = delivery_regressor.predict(
                DX_test
            )

            delivery_metrics = {
                "available": True,

                "target": (
                    "delivery days = delivered timestamp "
                    "minus purchase timestamp"
                ),

                "n_rows": int(len(duration_frame)),

                "n_test_rows": int(len(dy_test)),

                "rmse": float(
                    np.sqrt(
                        mean_squared_error(
                            dy_test,
                            duration_pred
                        )
                    )
                ),

                "mae": float(
                    mean_absolute_error(
                        dy_test,
                        duration_pred
                    )
                ),

                "r2": float(
                    r2_score(
                        dy_test,
                        duration_pred
                    )
                ),

                "split": (
                    "80/20 holdout; order-time features only"
                )
            }

    # -----------------------------------------------------
    # 10. SAVE MODEL BUNDLE AND OUTPUTS
    # -----------------------------------------------------

    odds = build_odds_ratios(classifier)

    data_status = data_loader.data_status()

    metrics = {
        "project": "Olist Sales & Customer Analytics",

        **main_metrics,

        "late_delivery_model": late_metrics,

        "delivery_time_model": delivery_metrics,

        "data_mode": data_status.get(
            "mode",
            "unknown"
        ),

        "data_source_message": data_status.get(
            "message",
            ""
        )
    }

    bundle = {
        "classifier": classifier,
        "regressor": regressor,
        "late_classifier": late_classifier,
        "delivery_regressor": delivery_regressor,
        "feature_columns": features.FEATURE_COLUMNS,
        "metrics": metrics,
        "odds_ratios": odds.to_dict("records"),
        "late_odds_ratios": late_odds.to_dict("records"),
        "target_definition": main_metrics["target"]
    }

    config.MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(
        bundle,
        config.MODEL_FILE
    )

    config.METRICS_FILE.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8"
    )

    odds.to_csv(
        config.ODDS_RATIOS_FILE,
        index=False
    )

    late_odds.to_csv(
        config.MODEL_DIR / "late_odds_ratios.csv",
        index=False
    )

    screening.to_csv(
        config.FEATURE_SCREENING_FILE,
        index=False
    )

    corr_df.to_csv(
        config.NUMERIC_CORRELATIONS_FILE,
        index=False
    )

    vif_df.to_csv(
        config.NUMERIC_VIF_FILE,
        index=False
    )

    # Save model comparison separately for easy inspection.
    pd.DataFrame(model_comparison).to_csv(
        config.MODEL_DIR / "model_comparison.csv",
        index=False
    )

    print("\n" + "=" * 55)
    print("OLIST MODEL TRAINING COMPLETED")
    print("=" * 55)

    print("\nMODEL COMPARISON")

    print(
        pd.DataFrame(model_comparison).to_string(
            index=False
        )
    )

    print("\nSELECTED MODEL:", selected_model)

    print(
        f"TEST ACCURACY: "
        f"{main_metrics['accuracy'] * 100:.2f}%"
    )

    print(
        f"BALANCED ACCURACY: "
        f"{main_metrics['balanced_accuracy'] * 100:.2f}%"
    )

    print(
        f"PRECISION: "
        f"{main_metrics['precision'] * 100:.2f}%"
    )

    print(
        f"RECALL: "
        f"{main_metrics['recall'] * 100:.2f}%"
    )

    print(
        f"F1 SCORE: "
        f"{main_metrics['f1'] * 100:.2f}%"
    )

    print(
        f"ROC-AUC: "
        f"{main_metrics['roc_auc'] * 100:.2f}%"
    )

    print("\nDUMMY BASELINE ACCURACY:",
          f"{metrics['dummy_baseline']['accuracy'] * 100:.2f}%")

    print("\nCONFUSION MATRIX:")
    print(np.array(main_metrics["confusion_matrix"]))

    print("\nSaved model:", config.MODEL_FILE)
    print("Saved metrics:", config.METRICS_FILE)

    return classifier, metrics, X_test, y_test


if __name__ == "__main__":
    train()
