"""Data structures and normalization helpers for the expense JSON format."""

import json
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Optional
from typing import Literal


DEFAULT_REPEAT_EVERY_UNIT: Literal["days", "weeks", "months", "years"] = "months"
DEFAULT_REPEAT_EVERY: int = 1
_VALID_REPEAT_UNITS = {"days", "weeks", "months", "years"}


@dataclass
class Expense:
    account_id: str
    name: str
    description: Optional[str]
    category: Optional[str]
    value: Optional[float]
    currency: Optional[str]
    repeat_every_unit: Literal["days", "weeks", "months", "years"]
    repeat_every: int = DEFAULT_REPEAT_EVERY
    monthly_value_eur: Optional[float] = None
    monthly_value: Optional[float] = None
    yearly_value_eur: Optional[float] = None
    yearly_value: Optional[float] = None


def load_expenses(expense_file: str | Path, accounts_file: Optional[str | Path] = None) -> List[Expense]:
    """Load expenses from *expense_file* and normalize them into Expense objects."""

    expense_path = Path(expense_file)
    accounts_path = (
        Path(accounts_file)
        if accounts_file is not None
        else expense_path.with_name("accounts.json")
    )

    if accounts_path.exists():
        with accounts_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        accounts = data.get("accounts", [])

    with expense_path.open("r", encoding="utf-8") as fh:
        raw_expenses = json.load(fh)

    expenses: List[Expense] = []

    for raw in raw_expenses:
        repeat_every = raw.get("repeat_every")
        expense = Expense(
                account_id=raw.get("account_id"),
                name=raw.get("name"),
                description=raw.get("description"),
                category=raw.get("category"),
                value=raw.get("value"),
                currency=raw.get("currency"),
                repeat_every_unit=raw.get("repeat_every_unit"),
                repeat_every=repeat_every if repeat_every is not None else DEFAULT_REPEAT_EVERY,
            )

        expense.monthly_value = normalize_value(expense, target_currency=None, target_time_unit="months")
        expense.monthly_value_eur = normalize_value(expense, target_currency="EUR", target_time_unit="months")
        expense.yearly_value = normalize_value(expense, target_currency=None, target_time_unit="years")
        expense.yearly_value_eur = normalize_value(expense, target_currency="EUR", target_time_unit="years")
        expenses.append(expense)

    return expenses

def normalize_value(expense: Expense, target_currency: Optional[str] = None, target_time_unit: Optional[Literal["days", "weeks", "months", "years"]] = None) -> float:
    fx_rate = get_fx_rate(expense.currency, target_currency)
    time_factor = time_conversion_factor(expense.repeat_every, expense.repeat_every_unit, target_time_unit)
    return expense.value * fx_rate * time_factor

def time_conversion_factor(interval: float, interval_unit: Literal["days", "weeks", "months", "years"], target_unit: Literal["days", "weeks", "months", "years"]) -> float:
    days_per_interval = interval * days_in_time_unit(interval_unit)
    days_per_target_unit = days_in_time_unit(target_unit)
    return days_per_target_unit / days_per_interval

def days_in_time_unit(time_unit: Literal["days", "weeks", "months", "years"]) -> float:
    return {
        "days": 1,
        "weeks": 7,
        "months": 146097 / 400 / 12, # Gregorian mean year / 12
        "years": 146097 / 400,       # Gregorian mean year
    }[time_unit]

def get_fx_rate(currency: Optional[str], target_currency: Optional[str]) -> float:
    """Get the FX rate for a given currency and target currency."""

    if not target_currency or not currency or currency == target_currency:
        return 1.0

    rates_to_eur = {
        "EUR": 1.0,
        "USD": 1 / 1.1570,
        "BRL": 1 / 6.1690,
    }

    if currency not in rates_to_eur or target_currency not in rates_to_eur:
        raise ValueError(f"Unsupported currency conversion: {currency} -> {target_currency}")

    value_in_eur = rates_to_eur[currency]
    if target_currency == "EUR":
        return value_in_eur
    return value_in_eur / rates_to_eur[target_currency]

def expenses_to_dataframe(expenses: List[Expense]) -> Any:
    """Transform a list of Expense objects into a pandas DataFrame."""

    pd = import_module("pandas")

    dataframe = pd.json_normalize([expense.__dict__ for expense in expenses])

    accounts_path = Path(__file__).with_name("accounts.json")
    if accounts_path.exists() and "account_id" in dataframe.columns:
        with accounts_path.open("r", encoding="utf-8") as fh:
            accounts_data = json.load(fh)
        order_map = {
            account["id"]: index
            for index, account in enumerate(accounts_data.get("accounts", []))
            if account.get("id")
        }
        if order_map:
            dataframe["__account_order"] = dataframe["account_id"].map(
                lambda account_id: order_map.get(account_id, len(order_map))
            )
            dataframe = dataframe.sort_values(
                by=["monthly_value_eur"],
                ascending=[False],
            ).drop(columns="__account_order")

    column_order = [
        "name",
        "category",
        "account_id",
        "yearly_value_eur",
        "monthly_value_eur",
        "yearly_value",
        "monthly_value",
        "currency",
        "value",
        "repeat_every",
        "repeat_every_unit",
    ]
    ordered_columns = [column for column in column_order if column in dataframe.columns]
    remaining_columns = [
        column for column in dataframe.columns if column not in ordered_columns
    ]

    for col in [
        "yearly_value_eur",
        "monthly_value_eur",
        "yearly_value",
        "monthly_value",
    ]:
        if col in dataframe.columns:
            dataframe[col] = dataframe[col].round(2)

    return dataframe.loc[:, ordered_columns + remaining_columns].reset_index(drop=True)
