"""Signal generation functions for rule-based analysis.

This module provides functions for applying rules to a DataFrame and generating
signals with reasons based on matching conditions.
"""

import pandas as pd
from pandas import DataFrame
from typing import List, Dict, Any, Callable


def generate_signals(df: DataFrame, rules: List[Dict[str, Any]]) -> DataFrame:
    """Generate signals by applying rules to DataFrame rows.

    Rules are evaluated in order, and the first matching rule's action is used as the signal.
    All matching rule names are recorded in the reasons field.

    Args:
        df: DataFrame to apply rules to. Each row will be evaluated against all rules.
        rules: List of rule dictionaries, each containing:
            - name: str - Rule name (used in reasons)
            - condition: Callable[[pd.Series], bool] - Condition function that takes a row
              and returns True if the rule matches
            - action: str - Signal action to apply when rule matches (e.g., "buy", "sell", "watch")

    Returns:
        DataFrame with added 'signal' and 'reasons' columns:
        - signal: str or NaN - Signal action from first matching rule, or NaN if no rules match
        - reasons: List[str] - List of all matching rule names
        Original DataFrame is not modified.

    Raises:
        KeyError: If a rule is missing required keys ('name', 'condition', 'action').
        ValueError: If condition function raises an exception.

    Examples:
        >>> df = pd.DataFrame({
        ...     'symbol': ['AAPL', 'MSFT'],
        ...     'return_pct': [6.0, 3.0]
        ... })
        >>> def high_return(row): return row['return_pct'] > 5.0
        >>> rules = [{'name': 'high_return', 'condition': high_return, 'action': 'buy'}]
        >>> result = generate_signals(df, rules)
        >>> result.loc[result['symbol'] == 'AAPL', 'signal'].iloc[0]
        'buy'
    """
    # Validate rules structure
    required_keys = {"name", "condition", "action"}
    for i, rule in enumerate(rules):
        missing_keys = required_keys - set(rule.keys())
        if missing_keys:
            raise KeyError(
                f"Rule at index {i} is missing required keys: {', '.join(missing_keys)}. "
                f"Required keys: {', '.join(required_keys)}"
            )

    # Create a copy to avoid side effects
    result_df = df.copy()

    # Initialize signal and reasons columns
    result_df["signal"] = pd.NA
    result_df["reasons"] = result_df.apply(lambda _: [], axis=1)

    # Apply rules to each row
    for idx, row in result_df.iterrows():
        matching_rules: List[str] = []
        signal_action = pd.NA

        # Evaluate rules in order (priority: first match wins for signal)
        for rule in rules:
            rule_name = rule["name"]
            condition_func = rule["condition"]
            action = rule["action"]

            try:
                # Evaluate condition (handle non-boolean returns by converting to bool)
                condition_result = condition_func(row)
                # Convert to boolean (handles truthy/falsy values)
                if pd.isna(condition_result):
                    condition_result = False
                else:
                    condition_result = bool(condition_result)

                if condition_result:
                    matching_rules.append(rule_name)
                    # First matching rule's action becomes the signal
                    if pd.isna(signal_action):
                        signal_action = action

            except Exception as e:
                # Re-raise exception with context
                raise ValueError(
                    f"Error evaluating rule '{rule_name}' for row at index {idx}: {str(e)}"
                ) from e

        # Set signal and reasons for this row
        result_df.at[idx, "signal"] = signal_action
        result_df.at[idx, "reasons"] = matching_rules

    return result_df

