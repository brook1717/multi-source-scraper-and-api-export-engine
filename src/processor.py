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
