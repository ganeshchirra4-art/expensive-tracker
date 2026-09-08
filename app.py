from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import datetime


# =========================================================
# FLASK SETUP
# =========================================================

app = Flask(__name__)

app.secret_key = "expense_tracker_secret_key"


# =========================================================
# FILE PATH
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

EXPENSES_FILE = os.path.join(
    BASE_DIR,
    "expenses.json"
)


# =========================================================
# LOAD EXPENSES
# =========================================================

def load_expenses():

    if (
        os.path.exists(EXPENSES_FILE)
        and os.path.getsize(EXPENSES_FILE) > 0
    ):

        try:

            with open(
                EXPENSES_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

        except (
            json.JSONDecodeError,
            OSError
        ):

            data = {
                "expenses": [],
                "budget": {}
            }

    else:

        data = {
            "expenses": [],
            "budget": {}
        }

    # Make sure both keys exist

    if "expenses" not in data:
        data["expenses"] = []

    if "budget" not in data:
        data["budget"] = {}

    return data


# =========================================================
# SAVE EXPENSES
# =========================================================

def save_expenses(data):

    with open(
        EXPENSES_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )


# =========================================================
# SAFE AMOUNT CONVERSION
# =========================================================

def get_amount(expense):

    try:

        return float(
            expense.get(
                "amount",
                0
            )
        )

    except (
        ValueError,
        TypeError
    ):

        return 0.0


# =========================================================
# GET EXPENSE MONTH
# =========================================================

def get_expense_month(expense):

    date = str(
        expense.get(
            "date",
            ""
        )
    )

    # YYYY-MM-DD

    if len(date) >= 7:

        return date[:7]

    return ""


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
def home():

    data = load_expenses()

    expenses = data.get(
        "expenses",
        []
    )

    budget = data.get(
        "budget",
        {}
    )

    # -----------------------------------------------------
    # CURRENT DATE
    # -----------------------------------------------------

    now = datetime.now()

    current_month_number = now.strftime(
        "%m"
    )

    current_month = now.strftime(
        "%B %Y"
    )

    current_month_key = now.strftime(
        "%Y-%m"
    )

    # -----------------------------------------------------
    # TOTAL EXPENSES
    # -----------------------------------------------------

    total_expenses = sum(
        get_amount(expense)
        for expense in expenses
    )

    # -----------------------------------------------------
    # THIS MONTH'S EXPENSES
    # -----------------------------------------------------

    monthly_expenses = []

    for expense in expenses:

        if get_expense_month(
            expense
        ) == current_month_key:

            monthly_expenses.append(
                expense
            )

    monthly_total = sum(
        get_amount(expense)
        for expense in monthly_expenses
    )

    # -----------------------------------------------------
    # TRANSACTION COUNT
    # -----------------------------------------------------

    transaction_count = len(
        expenses
    )

    # -----------------------------------------------------
    # MONTHLY BUDGET
    #
    # Original Python code stores budget
    # using month number: "01", "02", ... "12"
    # -----------------------------------------------------

    monthly_budget = float(
        budget.get(
            current_month_number,
            0
        )
    )

    # -----------------------------------------------------
    # REMAINING BUDGET
    # -----------------------------------------------------

    remaining_budget = (
        monthly_budget -
        monthly_total
    )

    # -----------------------------------------------------
    # CATEGORY TOTALS
    #
    # Current month only
    # -----------------------------------------------------

    category_totals = {}

    for expense in monthly_expenses:

        category = expense.get(
            "category",
            "Other"
        )

        category = str(
            category
        ).strip()

        if not category:

            category = "Other"

        amount = get_amount(
            expense
        )

        category_totals[category] = (
            category_totals.get(
                category,
                0
            ) + amount
        )

    # -----------------------------------------------------
    # SORT CATEGORY TOTALS
    # -----------------------------------------------------

    category_totals = dict(
        sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True
        )
    )

    # -----------------------------------------------------
    # RECENT EXPENSES
    # -----------------------------------------------------

    recent_expenses = sorted(
        expenses,
        key=lambda expense: expense.get(
            "date",
            ""
        ),
        reverse=True
    )[:5]

    # -----------------------------------------------------
    # RENDER DASHBOARD
    # -----------------------------------------------------

    return render_template(

        "dashboard.html",

        total_expenses=total_expenses,

        monthly_total=monthly_total,

        monthly_budget=monthly_budget,

        transaction_count=transaction_count,

        current_month=current_month,

        remaining_budget=remaining_budget,

        category_totals=category_totals,

        recent_expenses=recent_expenses,

        expenses=expenses
    )


# =========================================================
# ADD EXPENSE
# =========================================================

@app.route(
    "/add-expense",
    methods=["GET", "POST"]
)
def add_expense():

    data = load_expenses()

    expenses = data.get(
        "expenses",
        []
    )

    budget = data.get(
        "budget",
        {}
    )

    if request.method == "POST":

        # -------------------------------------------------
        # FORM VALUES
        # -------------------------------------------------

        description = request.form.get(
            "description",
            ""
        ).strip()

        category = request.form.get(
            "category",
            "Other"
        ).strip()

        amount_text = request.form.get(
            "amount",
            ""
        ).strip()

        date = request.form.get(
            "date",
            ""
        ).strip()

        # -------------------------------------------------
        # DESCRIPTION VALIDATION
        # -------------------------------------------------

        if not description:

            flash(
                "Please provide a description.",
                "error"
            )

            return render_template(
                "add_expense.html"
            )

        # -------------------------------------------------
        # AMOUNT VALIDATION
        # -------------------------------------------------

        try:

            amount = float(
                amount_text
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Please enter a valid amount.",
                "error"
            )

            return render_template(
                "add_expense.html"
            )

        if amount <= 0:

            flash(
                "Amount must be greater than 0.",
                "error"
            )

            return render_template(
                "add_expense.html"
            )

        # -------------------------------------------------
        # DATE
        # -------------------------------------------------

        if not date:

            date = datetime.now().strftime(
                "%Y-%m-%d"
            )

        else:

            try:

                datetime.strptime(
                    date,
                    "%Y-%m-%d"
                )

            except ValueError:

                flash(
                    "Please enter a valid date.",
                    "error"
                )

                return render_template(
                    "add_expense.html"
                )

        # -------------------------------------------------
        # MONTH
        # -------------------------------------------------

        month = date.split(
            "-"
        )[1]

        # -------------------------------------------------
        # CHECK MONTHLY BUDGET
        # -------------------------------------------------

        if month in budget:

            existing_month_total = sum(

                get_amount(expense)

                for expense in expenses

                if str(
                    expense.get(
                        "date",
                        ""
                    )
                ).startswith(
                    date[:7]
                )
            )

            if (
                existing_month_total +
                amount >
                float(budget[month])
            ):

                flash(
                    "Warning: This expense exceeds your monthly budget.",
                    "error"
                )

                return render_template(
                    "add_expense.html"
                )

        # -------------------------------------------------
        # CREATE ID
        # -------------------------------------------------

        if expenses:

            ids = []

            for expense in expenses:

                try:

                    ids.append(
                        int(
                            expense.get(
                                "id",
                                0
                            )
                        )
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    pass

            new_id = (
                max(ids) + 1
                if ids
                else 1
            )

        else:

            new_id = 1

        # -------------------------------------------------
        # CREATE EXPENSE
        # -------------------------------------------------

        expense = {

            "id": new_id,

            "date": date,

            "description": description,

            "amount": amount,

            "category": category,

            "month": month
        }

        # -------------------------------------------------
        # SAVE
        # -------------------------------------------------

        expenses.append(
            expense
        )

        data["expenses"] = expenses

        save_expenses(
            data
        )

        flash(
            "Expense added successfully!",
            "success"
        )

        return redirect(
            url_for("home")
        )

    # GET REQUEST

    return render_template(
        "add_expense.html"
    )


# =========================================================
# HISTORY
# =========================================================

@app.route("/history")
def history():

    data = load_expenses()

    expenses = data.get(
        "expenses",
        []
    )

    # Newest first

    expenses = sorted(
        expenses,
        key=lambda expense: expense.get(
            "date",
            ""
        ),
        reverse=True
    )

    return render_template(
        "history.html",
        expenses=expenses
    )


# =========================================================
# DELETE EXPENSE
# =========================================================

@app.route(
    "/delete-expense/<int:expense_id>",
    methods=["GET", "POST"]
)
def delete_expense(expense_id):

    data = load_expenses()

    expenses = data.get(
        "expenses",
        []
    )

    original_count = len(
        expenses
    )

    expenses = [

        expense

        for expense in expenses

        if int(
            expense.get(
                "id",
                0
            )
        ) != expense_id

    ]

    if len(expenses) < original_count:

        data["expenses"] = expenses

        save_expenses(
            data
        )

        flash(
            "Expense deleted successfully.",
            "success"
        )

    else:

        flash(
            "Expense not found.",
            "error"
        )

    return redirect(
        url_for("history")
    )


# =========================================================
# BUDGET
# =========================================================

@app.route(
    "/budget",
    methods=["GET", "POST"]
)
def budget_page():

    data = load_expenses()

    expenses = data.get(
        "expenses",
        []
    )

    budget = data.get(
        "budget",
        {}
    )

    # -----------------------------------------------------
    # SET BUDGET
    # -----------------------------------------------------

    if request.method == "POST":

        month = request.form.get(
            "month",
            ""
        ).strip()

        amount_text = request.form.get(
            "amount",
            ""
        ).strip()

        # -------------------------------------------------
        # MONTH VALIDATION
        # -------------------------------------------------

        try:

            month_number = int(
                month
            )

            if not 1 <= month_number <= 12:

                raise ValueError

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Please enter a valid month from 1 to 12.",
                "error"
            )

            return redirect(
                url_for("budget_page")
            )

        month = str(
            month_number
        ).zfill(2)

        # -------------------------------------------------
        # AMOUNT VALIDATION
        # -------------------------------------------------

        try:

            amount = float(
                amount_text
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Please enter a valid budget amount.",
                "error"
            )

            return redirect(
                url_for("budget_page")
            )

        if amount < 0:

            flash(
                "Budget cannot be negative.",
                "error"
            )

            return redirect(
                url_for("budget_page")
            )

        # -------------------------------------------------
        # SAVE BUDGET
        # -------------------------------------------------

        budget[month] = amount

        data["budget"] = budget

        save_expenses(
            data
        )

        flash(
            f"Budget for month {month} updated successfully!",
            "success"
        )

        return redirect(
            url_for("budget_page")
        )

    # -----------------------------------------------------
    # CURRENT MONTH
    # -----------------------------------------------------

    current_month_number = datetime.now().strftime(
        "%m"
    )

    current_month = datetime.now().strftime(
        "%B %Y"
    )

    current_month_key = datetime.now().strftime(
        "%Y-%m"
    )

    # -----------------------------------------------------
    # CURRENT MONTH EXPENSES
    # -----------------------------------------------------

    monthly_expenses = [

        expense

        for expense in expenses

        if get_expense_month(
            expense
        ) == current_month_key

    ]

    # -----------------------------------------------------
    # TOTAL SPENT
    # -----------------------------------------------------

    total_spent = sum(
        get_amount(expense)
        for expense in monthly_expenses
    )

    # -----------------------------------------------------
    # MONTHLY BUDGET
    # -----------------------------------------------------

    monthly_budget = float(
        budget.get(
            current_month_number,
            0
        )
    )

    # -----------------------------------------------------
    # REMAINING
    # -----------------------------------------------------

    remaining_budget = (
        monthly_budget -
        total_spent
    )

    # -----------------------------------------------------
    # PERCENTAGE
    # -----------------------------------------------------

    if monthly_budget > 0:

        budget_percentage = (
            total_spent /
            monthly_budget
        ) * 100

    else:

        budget_percentage = 0

    display_percentage = min(
        max(
            budget_percentage,
            0
        ),
        100
    )

    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

    return render_template(

        "budget.html",

        expenses=expenses,

        monthly_expenses=monthly_expenses,

        budget=budget,

        budgets=budget,

        monthly_budget=monthly_budget,

        total_spent=total_spent,

        monthly_total=total_spent,

        remaining_budget=remaining_budget,

        budget_percentage=budget_percentage,

        display_percentage=display_percentage,

        current_month=current_month,

        current_month_number=current_month_number
    )


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
def reports():

    data = load_expenses()

    expenses = data.get(
        "expenses",
        []
    )

    budget = data.get(
        "budget",
        {}
    )

    # -----------------------------------------------------
    # TOTAL EXPENSES
    # -----------------------------------------------------

    total_expenses = sum(
        get_amount(expense)
        for expense in expenses
    )

    # -----------------------------------------------------
    # CATEGORY TOTALS
    # -----------------------------------------------------

    category_totals = {}

    for expense in expenses:

        category = expense.get(
            "category",
            "Other"
        )

        category = str(
            category
        ).strip()

        if not category:

            category = "Other"

        amount = get_amount(
            expense
        )

        category_totals[category] = (
            category_totals.get(
                category,
                0
            ) + amount
        )

    # -----------------------------------------------------
    # MONTHLY SPENDING
    # -----------------------------------------------------

    monthly_spending = {}

    for expense in expenses:

        month_key = get_expense_month(
            expense
        )

        if not month_key:

            continue

        amount = get_amount(
            expense
        )

        monthly_spending[month_key] = (
            monthly_spending.get(
                month_key,
                0
            ) + amount
        )

    # -----------------------------------------------------
    # CURRENT MONTH
    # -----------------------------------------------------

    current_month_key = datetime.now().strftime(
        "%Y-%m"
    )

    current_month_number = datetime.now().strftime(
        "%m"
    )

    current_month_total = monthly_spending.get(
        current_month_key,
        0
    )

    monthly_budget = float(
        budget.get(
            current_month_number,
            0
        )
    )

    remaining_budget = (
        monthly_budget -
        current_month_total
    )

    # -----------------------------------------------------
    # TRANSACTION COUNT
    # -----------------------------------------------------

    transaction_count = len(
        expenses
    )

    # -----------------------------------------------------
    # AVERAGE
    # -----------------------------------------------------

    if transaction_count > 0:

        average_expense = (
            total_expenses /
            transaction_count
        )

    else:

        average_expense = 0

    # -----------------------------------------------------
    # HIGHEST EXPENSE
    # -----------------------------------------------------

    if expenses:

        highest_expense = max(
            expenses,
            key=get_amount
        )

        highest_expense_amount = get_amount(
            highest_expense
        )

    else:

        highest_expense = None

        highest_expense_amount = 0

    # -----------------------------------------------------
    # SORT
    # -----------------------------------------------------

    category_totals = dict(
        sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True
        )
    )

    monthly_spending = dict(
        sorted(
            monthly_spending.items()
        )
    )

    # -----------------------------------------------------
    # CHART DATA
    # -----------------------------------------------------

    category_labels = list(
        category_totals.keys()
    )

    category_values = list(
        category_totals.values()
    )

    month_labels = list(
        monthly_spending.keys()
    )

    month_values = list(
        monthly_spending.values()
    )

    # -----------------------------------------------------
    # RENDER REPORT
    # -----------------------------------------------------

    return render_template(

        "reports.html",

        expenses=expenses,

        total_expenses=total_expenses,

        transaction_count=transaction_count,

        average_expense=average_expense,

        highest_expense=highest_expense,

        highest_expense_amount=highest_expense_amount,

        category_totals=category_totals,

        monthly_spending=monthly_spending,

        category_labels=category_labels,

        category_values=category_values,

        month_labels=month_labels,

        month_values=month_values,

        budgets=budget,

        budget=budget,

        monthly_budget=monthly_budget,

        current_month_total=current_month_total,

        monthly_total=current_month_total,

        remaining_budget=remaining_budget
    )


# =========================================================
# ANALYTICS
# =========================================================

@app.route("/analytics")
def analytics():

    data = load_expenses()

    expenses = data.get(
        "expenses",
        []
    )

    # -----------------------------------------------------
    # CATEGORY TOTALS
    # -----------------------------------------------------

    category_totals = {}

    for expense in expenses:

        category = expense.get(
            "category",
            "Other"
        )

        amount = get_amount(
            expense
        )

        category_totals[category] = (
            category_totals.get(
                category,
                0
            ) + amount
        )

    # -----------------------------------------------------
    # MONTHLY TOTALS
    # -----------------------------------------------------

    monthly_spending = {}

    for expense in expenses:

        month = get_expense_month(
            expense
        )

        if not month:

            continue

        amount = get_amount(
            expense
        )

        monthly_spending[month] = (
            monthly_spending.get(
                month,
                0
            ) + amount
        )

    # -----------------------------------------------------
    # TOTAL
    # -----------------------------------------------------

    total_expenses = sum(
        category_totals.values()
    )

    transaction_count = len(
        expenses
    )

    # -----------------------------------------------------
    # AVERAGE
    # -----------------------------------------------------

    if transaction_count:

        average_expense = (
            total_expenses /
            transaction_count
        )

    else:

        average_expense = 0

    # -----------------------------------------------------
    # TOP CATEGORY
    # -----------------------------------------------------

    if category_totals:

        top_category = max(
            category_totals,
            key=category_totals.get
        )

        top_category_amount = (
            category_totals[
                top_category
            ]
        )

    else:

        top_category = "No data"

        top_category_amount = 0

    # -----------------------------------------------------
    # CHART DATA
    # -----------------------------------------------------

    category_labels = list(
        category_totals.keys()
    )

    category_values = list(
        category_totals.values()
    )

    month_labels = list(
        monthly_spending.keys()
    )

    month_values = list(
        monthly_spending.values()
    )

    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

    return render_template(

        "analytics.html",

        expenses=expenses,

        total_expenses=total_expenses,

        transaction_count=transaction_count,

        average_expense=average_expense,

        top_category=top_category,

        top_category_amount=top_category_amount,

        category_totals=category_totals,

        monthly_spending=monthly_spending,

        category_labels=category_labels,

        category_values=category_values,

        month_labels=month_labels,

        month_values=month_values
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )