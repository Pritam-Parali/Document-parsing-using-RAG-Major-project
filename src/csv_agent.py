import pandas as pd


def analyze_csv(query: str, csv_path: str):
    """
    Handle CSV-related analytical queries using pandas.
    Returns an answer string if query can be handled,
    otherwise returns None.
    """

    try:
        df = pd.read_csv(csv_path)

        query = query.lower()

        # Rows and columns
        if "rows" in query and "columns" in query:
            return f"The CSV contains {df.shape[0]} rows and {df.shape[1]} columns."

        if "rows" in query:
            return f"The CSV contains {df.shape[0]} rows."

        if "columns" in query:
            return f"The CSV contains {df.shape[1]} columns."

        # Column names
        if "column names" in query or "headers" in query:
            return f"Columns: {', '.join(df.columns)}"

        # Find column mentioned in query
        matched_column = None

        for col in df.columns:
            if col.lower() in query:
                matched_column = col
                break

        if not matched_column:
            return None

        # Numeric operations only
        if not pd.api.types.is_numeric_dtype(df[matched_column]):
            return f"'{matched_column}' is not a numeric column."

        # Sum
        if "sum" in query:
            return f"Sum of {matched_column} = {df[matched_column].sum()}"

        # Average / Mean
        if "average" in query or "mean" in query:
            return f"Average of {matched_column} = {df[matched_column].mean()}"

        # Maximum
        if "max" in query or "maximum" in query:
            return f"Maximum value in {matched_column} = {df[matched_column].max()}"

        # Minimum
        if "min" in query or "minimum" in query:
            return f"Minimum value in {matched_column} = {df[matched_column].min()}"

        # Count
        if "count" in query:
            return f"Count of {matched_column} = {df[matched_column].count()}"

        # Median
        if "median" in query:
            return f"Median of {matched_column} = {df[matched_column].median()}"

        # Standard deviation
        if "std" in query or "standard deviation" in query:
            return f"Standard deviation of {matched_column} = {df[matched_column].std()}"

        return None

    except Exception as e:
        print(f"CSV Analysis Error: {e}")
        return None