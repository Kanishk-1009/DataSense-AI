import pandas as pd


def detect_column_type(series: pd.Series) -> str:
    non_null = series.dropna()

    if non_null.empty:
        return "unknown"

    if pd.api.types.is_bool_dtype(series):
        return "binary"

    if pd.api.types.is_numeric_dtype(series):
        unique = set(non_null.unique())

        if unique.issubset({0, 1}):
            return "binary"

        return "numeric"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    return "categorical"


def profile_dataset(df: pd.DataFrame) -> dict:
    duplicate_rows = int(df.duplicated().sum())

    profile = {
        "dataset_info": {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "duplicate_rows": duplicate_rows
        },
        "columns": {},
        "missing_values": {},
        "numeric_statistics": {},
        "categorical_statistics": {},
        "warnings": []
    }

    if duplicate_rows > 0:
        profile["warnings"].append(
            f"Dataset contains {duplicate_rows} duplicate row(s)."
        )

    for column in df.columns:

        column_type = detect_column_type(df[column])
        unique_values = int(df[column].nunique(dropna=True))

        profile["columns"][column] = {
            "dtype": str(df[column].dtype),
            "column_type": column_type,
            "unique_values": unique_values
        }

        if column_type == "categorical":

            mode = df[column].mode(dropna=True)

            if not mode.empty:
                most_frequent = mode.iloc[0]
                frequency = int(df[column].value_counts().iloc[0])
            else:
                most_frequent = None
                frequency = 0

            profile["categorical_statistics"][column] = {
                "most_frequent": most_frequent,
                "frequency": frequency
            }

        missing_count = int(df[column].isna().sum())

        missing_percentage = (
            missing_count / len(df) * 100
            if len(df) > 0
            else 0
        )

        profile["missing_values"][column] = {
            "count": missing_count,
            "percentage": round(missing_percentage, 2)
        }

        if missing_count > 0:
            profile["warnings"].append(
                f"{column} contains {missing_count} missing value(s)."
            )

        if unique_values <= 1:
            profile["warnings"].append(
                f"{column} is a constant column."
            )

        if column_type == "categorical":

            if unique_values > len(df) * 0.8:
                profile["warnings"].append(
                    f"{column} has very high cardinality."
                )

            if unique_values == len(df):
                profile["warnings"].append(
                    f"{column} may be an identifier column."
                )

            sample = df[column].dropna().astype(str).head(10)

            looks_like_date = sample.str.contains(
                r"[-/:]",
                regex=True
            ).any()

            if looks_like_date:

                parsed = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

                success_ratio = parsed.notna().mean()

                if success_ratio >= 0.8:
                    profile["warnings"].append(
                        f"{column} may contain datetime values."
                    )

        if column_type == "binary":

            counts = df[column].value_counts(dropna=True)

            if len(counts) == 2:

                ratio = counts.max() / counts.sum()

                if ratio > 0.90:
                    profile["warnings"].append(
                        f"{column} is highly imbalanced."
                    )

    return profile