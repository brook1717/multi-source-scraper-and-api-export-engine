import pandas as pd
import numpy as np

from src.logger import setup_logger

logger = setup_logger(__name__)


class DataProcessor:
    """Loads raw data into a DataFrame and provides cleaning utilities."""

    def __init__(self):
        self.df: pd.DataFrame = pd.DataFrame()

    def load_data(self, raw_data: list[dict]) -> pd.DataFrame:
        """Convert a list of dictionaries into a Pandas DataFrame."""
        if not raw_data:
            logger.warning("No data provided to load_data.")
            self.df = pd.DataFrame()
            return self.df

        self.df = pd.DataFrame(raw_data)
        logger.info("Loaded %d records with %d columns.", len(self.df), len(self.df.columns))
        return self.df

    def clean_data(self) -> pd.DataFrame:
        """Clean the DataFrame: strip whitespace from strings and fill NaN values."""
        if self.df.empty:
            logger.warning("DataFrame is empty. Nothing to clean.")
            return self.df

        # Strip leading/trailing whitespace from string columns
        string_cols = self.df.select_dtypes(include=["object"]).columns
        for col in string_cols:
            self.df[col] = self.df[col].map(
                lambda x: x.strip() if isinstance(x, str) else x
            )

        # Fill NaN based on column dtype
        for col in self.df.columns:
            if self.df[col].dtype == "object":
                self.df[col] = self.df[col].fillna("N/A")
            elif np.issubdtype(self.df[col].dtype, np.number):
                self.df[col] = self.df[col].fillna(0)
            else:
                self.df[col] = self.df[col].fillna("N/A")

        logger.info("Data cleaned: whitespace stripped, NaN values filled.")
        return self.df

    def deduplicate(self, subset_keys: list[str] | None = None) -> pd.DataFrame:
        """Drop duplicate rows from the DataFrame.

        If *subset_keys* is provided, duplicates are identified based on those
        columns only; otherwise the entire row is evaluated.
        """
        if self.df.empty:
            logger.warning("DataFrame is empty. Nothing to deduplicate.")
            return self.df

        before_count = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset_keys, keep="first").reset_index(drop=True)
        removed = before_count - len(self.df)
        logger.info("Deduplication complete: %d duplicate row(s) removed.", removed)
        return self.df

    def apply_filter(self, filter_key: str, filter_value: str) -> pd.DataFrame:
        """Filter the DataFrame where *filter_key* column contains *filter_value*.

        Uses case-insensitive string matching for string columns.
        Returns the filtered DataFrame (does not mutate self.df).
        """
        if not filter_key or not filter_value:
            logger.warning("Both filter_key and filter_value must be provided. Returning unfiltered data.")
            return self.df

        if filter_key not in self.df.columns:
            logger.warning("Column '%s' not found in DataFrame. Returning unfiltered data.", filter_key)
            return self.df

        col = self.df[filter_key]

        if pd.api.types.is_string_dtype(col):
            mask = col.str.contains(filter_value, case=False, na=False)
        else:
            mask = col == filter_value

        filtered_df = self.df[mask].reset_index(drop=True)
        logger.info(
            "Filter applied: column='%s', value='%s' -> %d of %d rows matched.",
            filter_key, filter_value, len(filtered_df), len(self.df),
        )
        return filtered_df
