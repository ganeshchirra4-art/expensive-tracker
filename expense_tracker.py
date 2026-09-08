import json
import os
from datetime import datetime

# Function to load expenses from the JSON file
def load_expenses():
    if os.path.exists('expenses.json') and os.path.getsize('expenses.json') > 0:  # Check if file exists and is not empty
        with open('expenses.json', 'r') as file:
            return json.load(file)
    return {"expenses": [], "budget": {}}  # Return empty expenses and budget if file doesn't exist or is empty

# Function to save expenses to the JSON file
def save_expenses(expenses_data):  # Modified to take a dictionary that includes expenses and budget
    with open("expenses.json", "w") as file:
        json.dump(expenses_data, file, indent=4)

# Function to add a new expense with customizable date
def add_expense(description, amount, category):
    if not description:
        print("Provide a description")
        return

    if amount <= 0:
        print("How are you printing -ve amount?")
        return

    # Load existing expenses and budget from JSON file
    data = load_expenses()
    expenses = data["expenses"]
    budget = data["budget"]

    try:
        # Ask user if they want to use today's date
        use_today = input("Do you want to use today's date? (y/n): ").strip().lower()

        if use_today == 'y':
            # Use today's date if the user chooses to
            date = datetime.now().strftime("%Y-%m-%d")  # Default to today's date
        else:
            # Prompt the user to input the specific year, month, and day
            year = input("Enter the year (YYYY): ")
            while not year.isdigit() or len(year) != 4:
                print("Invalid year. Please enter a valid 4-digit year.")
                year = input("Enter the year (YYYY): ")

            # Validate month
            month = input("Enter the month (MM): ")
            while not month.isdigit() or not (1 <= int(month) <= 12):
                print("Invalid month. Please enter a valid month (01-12).")
                month = input("Enter the month (MM): ")
            month = str(month).zfill(2)  # Ensure month is in two digits (e.g., 01, 02, ..., 12)

            # Validate day
            day = input("Enter the day (DD): ")
            while not day.isdigit() or not (1 <= int(day) <= 31):
                print("Invalid day. Please enter a valid day (01-31).")
                day = input("Enter the day (DD): ")
            day = str(day).zfill(2)  # Ensure day is in two digits (e.g., 01, 02, ..., 31)

            # Construct the full date string (YYYY-MM-DD)
            date = f"{year}-{month}-{day}"

    except Exception as e:
        print(f"An error occurred while adding expense: {e}")
        return

    # Check if the current month's expense exceeds the budget
    month = date.split("-")[1]  # Extract month from the date
    if month in budget and (sum(expense['amount'] for expense in expenses if expense['date'].split('-')[1] == month) + amount) > budget[month]:
        print(f"Warning: You are exceeding your budget for month {month}!")
        return

    # Create the new expense
    expense = {
        "id": len(expenses) + 1,
        "date": date,  # Set the correct date here
        "description": description,
        "amount": amount,
        "category": category,
        "month": month  # Store the month in 2-digit format
    }

    # Add new expense to the list
    expenses.append(expense)

    # Save the updated list of expenses and the budget
    data["expenses"] = expenses
    save_expenses(data)
    print(f"Expense added successfully (ID: {expense['id']})")

# Function to list all expenses, with optional category filter
def list_expenses(category=None):
    expenses_data = load_expenses()
    expenses = expenses_data["expenses"]

    if not expenses:
        print("No expenses found!")
        return

    if category:
        expenses = [expense for expense in expenses if expense['category'].lower() == category.lower()]

    if not expenses:
        print(f"No expenses found for category '{category}'!")
        return

    print("\nID   Date       Description  Amount  Category")
    print("-" * 50)
    for expense in expenses:
        print(f"{expense['id']: <5} {expense['date']}  {expense['description']: <15} ${expense['amount']: >7.2f}  {expense['category']}")

# Function to delete an expense by ID
def delete_expense(expense_id):
    expenses_data = load_expenses()
    expenses = expenses_data["expenses"]

    # Find the expense by ID
    expense_to_delete = None
    for expense in expenses:
        if expense["id"] == expense_id:
            expense_to_delete = expense
            break

    if expense_to_delete:
        expenses.remove(expense_to_delete)
        expenses_data["expenses"] = expenses
        save_expenses(expenses_data)
        print(f"Expense with ID {expense_id} deleted successfully.")
    else:
        print(f"Expense with ID {expense_id} not found.")

# Function to see summary of all expenses or by category, with budget info
def summary_expenses(month=None, category=None):
    expenses_data = load_expenses()
    expenses = expenses_data["expenses"]
    budget = expenses_data["budget"]
    total = 0
    if not expenses:
        print("No expenses found!")
        return

    # Filter by month if provided
    if month:
        month = str(month).zfill(2)  # Ensure month is in 2-digit format
        expenses = [expense for expense in expenses if expense['date'].split('-')[1] == month]

    # Filter by category if provided
    if category:
        expenses = [expense for expense in expenses if expense['category'].lower() == category.lower()]

    if expenses:
        print("\nID   Date       Description  Amount  Category")
        print("-" * 50)
        for expense in expenses:
            print(f"{expense['id']: <5} {expense['date']}  {expense['description']: <15} ${expense['amount']: >7.2f}  {expense['category']}")
        total = sum(expense['amount'] for expense in expenses)
        if month:
            print(f"\nTotal for month {month}: ${total:.2f}")
        elif category:
            print(f"\nTotal for category {category}: ${total:.2f}")
        else:
            print(f"\nTotal expenses: ${total:.2f}")
    else:
        print(f"No expenses found for the given filters!")

    if month in budget:
        print(f"Budget for month {month}: ${budget[month]:.2f}")
        print(f"Remaining budget: ${budget[month] - total:.2f}")
    else:
        print(f"No budget set for month {month}.")

# Function to set a budget for a month
def set_budget(month, amount):
    expenses_data = load_expenses()
    budget = expenses_data["budget"]
    
    # Ensure month is in 2-digit format
    month = str(month).zfill(2)
    budget[month] = amount
    expenses_data["budget"] = budget
    save_expenses(expenses_data)
    print(f"Budget for month {month} set to ${amount:.2f}")

# Function to report spending by category
def report_by_category(month=None):
    expenses_data = load_expenses()
    expenses = expenses_data["expenses"]
    category_totals = {}

    if month:
        month = str(month).zfill(2)  # Ensure month is in 2-digit format
        expenses = [expense for expense in expenses if expense['date'].split('-')[1] == month]

    if not expenses:
        print(f"No expenses found for month {month}!" if month else "No expenses found!")
        return

    for expense in expenses:
        category = expense['category'].lower()
        category_totals[category] = category_totals.get(category, 0) + expense['amount']

    print("\nCategory-wise Expense Summary:")
    for category, total in category_totals.items():
        print(f"{category.title()}: ${total:.2f}")

    total_expense = sum(category_totals.values())
    print(f"\nTotal Expense: ${total_expense:.2f}")

# Function to generate a spending trend report
def spending_trend():
    expenses_data = load_expenses()
    expenses = expenses_data["expenses"]
    monthly_spending = {}

    for expense in expenses:
        month = expense['date'].split('-')[1]
        monthly_spending[month] = monthly_spending.get(month, 0) + expense['amount']

    print("\nMonthly Spending Trend:")
    for month, total in sorted(monthly_spending.items()):
        print(f"Month {month}: ${total:.2f}")

    total_spent = sum(monthly_spending.values())
    print(f"\nTotal Spent: ${total_spent:.2f}")

# Function to show detailed summary with budget info
def detailed_summary():
    expenses_data = load_expenses()
    expenses = expenses_data["expenses"]
    budget = expenses_data["budget"]
    
    monthly_summary = {}

    for expense in expenses:
        month = expense['date'].split('-')[1]
        if month not in monthly_summary:
            monthly_summary[month] = {'total_spent': 0, 'expenses': []}
        monthly_summary[month]['total_spent'] += expense['amount']
        monthly_summary[month]['expenses'].append(expense)

    print("\nDetailed Monthly Summary:")
    for month, summary in sorted(monthly_summary.items()):
        print(f"\nMonth {month}:")
        for expense in summary['expenses']:
            print(f"{expense['id']}  {expense['date']}  {expense['description']}  ${expense['amount']:.2f}  {expense['category']}")
        
        total_spent = summary['total_spent']
        print(f"Total Spent in Month {month}: ${total_spent:.2f}")
        
        if month in budget:
            print(f"Budget for Month {month}: ${budget[month]:.2f}")
            print(f"Remaining Budget: ${budget[month] - total_spent:.2f}")
        else:
            print(f"No budget set for Month {month}.")

# Main function to interact with the user
def main():
    while True:
        print("\nExpense Tracker")
        print("1. Add expense")
        print("2. List expenses")
        print("3. Delete expense")
        print("4. Summary")
        print("5. Set budget")
        print("6. Report by category")
        print("7. Spending trend")
        print("8. Detailed summary")
        print("9. Exit")

        try:
            # User chooses an option
            choice = input("Enter your choice (1/2/3/4/5/6/7/8/9): ")

            if choice == "1":
                description = input("Enter expense description: ")
                try:
                    amount = float(input("Enter expense amount: "))
                    category = input("Enter expense category (e.g., Food, Transport, Utilities): ")
                    add_expense(description, amount, category)
                except ValueError:
                    print("Please provide a valid number for the amount.")
                    continue

            elif choice == "2":
                category = input("Enter category to filter by (or press enter to list all): ")
                list_expenses(category)

            elif choice == "3":
                expense_id = int(input("Enter the ID of the expense to delete: "))
                delete_expense(expense_id)

            elif choice == "4":
                month_input = input("Enter the month to view summary (or press enter to view all): ")
                category_input = input("Enter category to view summary (or press enter to view all): ")
                summary_expenses(month=month_input, category=category_input)

            elif choice == "5":
                month = input("Enter the month to set the budget for: ")
                budget = float(input("Enter the budget amount: "))
                set_budget(month, budget)

            elif choice == "6":
                month = input("Enter the month for the category report (or press enter for all): ")
                report_by_category(month)

            elif choice == "7":
                spending_trend()

            elif choice == "8":
                detailed_summary()

            elif choice == "9":
                print("Exiting...")
                break

            else:
                print("Invalid choice.")

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()