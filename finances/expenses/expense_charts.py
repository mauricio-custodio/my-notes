import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd


def create_category_color_map(df):
    expense_categories_all = df['category'] if 'category' in df.columns else None
    if expense_categories_all is not None:
        unique_categories_all = [cat for cat in pd.unique(expense_categories_all) if pd.notnull(cat)]
        unique_categories_all = sorted(unique_categories_all)
    else:
        unique_categories_all = []
    available_colors = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["skyblue", "C1", "C2", "C3", "C4", "C5", "C6", "C7"])
    return {cat: available_colors[i % len(available_colors)] for i, cat in enumerate(unique_categories_all)}


def plot_expenses_waterfall(df):
    category_color_map = create_category_color_map(df)
    
    expense_values = df['monthly_value_eur'] if 'monthly_value_eur' in df.columns else df['monthly_value']
    expense_names = df['name']
    expense_categories = df['category'] if 'category' in df.columns else None

    sorted_indices = np.argsort(expense_values.values)
    expense_names_sorted = expense_names.values[sorted_indices]
    expense_values_sorted = expense_values.values[sorted_indices]
    expense_categories_sorted = expense_categories.values[sorted_indices] if expense_categories is not None else ["Other"] * len(expense_names_sorted)

    cumulative = np.cumsum(expense_values_sorted) - expense_values_sorted

    rent_idx = np.where(expense_names_sorted == "Rent")[0]
    if len(rent_idx) == 0:
        insert_at = 0
    else:
        insert_at = rent_idx[0] + 1

    all_names = list(expense_names_sorted)
    all_values = list(expense_values_sorted)
    all_cumulative = list(cumulative)
    all_categories = list(expense_categories_sorted)

    all_names.insert(insert_at, "TOTAL")
    all_values.insert(insert_at, expense_values_sorted.sum())
    all_cumulative.insert(insert_at, 0)
    all_categories.insert(insert_at, "Total")

    total_value = expense_values_sorted.sum()

    bar_colors = []
    for i, cat in enumerate(all_categories):
        if i == insert_at:
            bar_colors.append("orange")
        else:
            bar_colors.append(category_color_map.get(cat, "grey"))

    label_colors = []
    for i, cat in enumerate(all_categories):
        if i == insert_at:
            label_colors.append("orange")
        else:
            label_colors.append(category_color_map.get(cat, "grey"))

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.barh(all_names, all_values, left=all_cumulative, color=bar_colors)

    ax.set_xlabel('Monthly Value (EUR)')
    ax.set_ylabel('Expense Name')
    ax.set_title('Monthly Expenses Waterfall (EUR)')

    for i, (bar, value, label_color) in enumerate(zip(bars, all_values, label_colors)):
        percent = int(round(100 * value / total_value)) if total_value > 0 else 0
        label_text = f'{int(round(value))} - {percent}%'
        if i == insert_at:
            ax.text(bar.get_x() + bar.get_width() + 0.05,
                    bar.get_y() + bar.get_height() / 2,
                    label_text, va='center', ha='left', fontweight='bold')
        else:
            ax.text(bar.get_x() + bar.get_width() + 0.05,
                    bar.get_y() + bar.get_height() / 2,
                    label_text, va='center', ha='left')

    yticks = ax.get_yticklabels()
    for i, tick in enumerate(yticks):
        if i < len(label_colors):
            tick.set_color(label_colors[i])

    legend_handles = [mpatches.Patch(color=color, label=cat) for cat, color in category_color_map.items()]
    legend_handles.insert(0, mpatches.Patch(color="orange", label="TOTAL"))

    ax.legend(handles=legend_handles, title="Categories", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()
    plt.show(fig)


def plot_category_waterfall(df):
    category_color_map = create_category_color_map(df)
    
    expense_values = df['monthly_value_eur'] if 'monthly_value_eur' in df.columns else df['monthly_value']
    expense_categories = df['category']

    category_sums = expense_values.groupby(expense_categories).sum()

    category_sums = category_sums[category_sums.index.notnull()]

    sorted_indices = np.argsort(category_sums.values)
    categories_sorted = category_sums.index.values[sorted_indices]
    values_sorted = category_sums.values[sorted_indices]

    cumulative = np.cumsum(values_sorted) - values_sorted

    housing_idx = np.where(categories_sorted == "Housing")[0]
    if len(housing_idx) == 0:
        insert_at = 0
    else:
        insert_at = housing_idx[0] + 1

    all_names = list(categories_sorted)
    all_values = list(values_sorted)
    all_cumulative = list(cumulative)

    all_names.insert(insert_at, "TOTAL")
    all_values.insert(insert_at, values_sorted.sum())
    all_cumulative.insert(insert_at, 0)

    total_value = values_sorted.sum()

    bar_colors = []
    for i, name in enumerate(all_names):
        if i == insert_at:
            bar_colors.append("orange")
        else:
            bar_colors.append(category_color_map.get(name, "grey"))

    label_colors = []
    for i, name in enumerate(all_names):
        if i == insert_at:
            label_colors.append("orange")
        else:
            label_colors.append(category_color_map.get(name, "grey"))

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.barh(all_names, all_values, left=all_cumulative, color=bar_colors)

    ax.set_xlabel('Monthly Value (EUR)')
    ax.set_ylabel('Expense Category')
    ax.set_title('Monthly Expenses by Category Waterfall (EUR)')

    for i, (bar, value, label_color) in enumerate(zip(bars, all_values, label_colors)):
        percent = int(round(100 * value / total_value)) if total_value > 0 else 0
        label_text = f'{int(round(value))} - {percent}%'
        if i == insert_at:
            ax.text(bar.get_x() + bar.get_width() + 0.05,
                    bar.get_y() + bar.get_height() / 2,
                    label_text, va='center', ha='left', fontweight='bold')
        else:
            ax.text(bar.get_x() + bar.get_width() + 0.05,
                    bar.get_y() + bar.get_height() / 2,
                    label_text, va='center', ha='left')

    yticks = ax.get_yticklabels()
    for i, tick in enumerate(yticks):
        if i < len(label_colors):
            tick.set_color(label_colors[i])

    legend_handles = [mpatches.Patch(color=color, label=cat) for cat, color in category_color_map.items()]
    legend_handles.insert(0, mpatches.Patch(color="orange", label="TOTAL"))

    ax.legend(handles=legend_handles, title="Categories", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()
    plt.show(fig)

