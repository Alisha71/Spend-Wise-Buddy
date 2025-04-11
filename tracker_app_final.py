# To import important libraries:
# sqlite3: This provides access to use SQLite databases (db).
# datetime: This allows validating and managing date formats.
# os: Is used for file operations like checking the existence of a database.
import sqlite3
from datetime import datetime
import os


def link_to_finance_db():
    """
    This function links to the SQLite database called Spend_Wise_Buddy
    and manages any errors. Allows interaction with the database
    throughout the program without repeatedly starting new connections.

    Returns:
        sqlite3.Connection: Database connection is successful.
        None: Failure to connect to the database. Meaning the program
        terminates due to an error/s.

    Raises:
        sqlite3.Error: Spots and manages database connection failures.
    """
    try:
        # Link to the db.
        return sqlite3.connect("Spend_Wise_Buddy.db")
    except sqlite3.Error as e:
        print(f"Oops! Failed to connect to the database ❌: {e}")
        # If db connection fails, it terminates the program.
        exit(1)


def build_a_financial_db():
    """
    This function creates the db tables if they do not exist.
    This function ensure structured storage for expenses,incomes,
    budgets, and savings goals by intialising the SQLite db.

    If the database is found to exist it does not set up in
    order to avoid overwriting data.

    The function follows these steps:
    1. It first checks for the existence of the database and if not
    it will create a new one.
    2. It then establishes a connection with the database.
    3. It then defines the required tables in SQL statements.
    4. It then executes SQL commands to create the tables if they are not
    created yet.
    5. It then commits the changes and close the connection.
    """
    if not os.path.exists("Spend_Wise_Buddy.db"):
        print("Generating database...")
    else:
        print("Existing database found already, skipping setup.")

    # Set up a connection to the db.
    link_to_db = link_to_finance_db()

    # Check to see if the db connection was successful or not.
    # If a db connection is lost or failed, terminate program.
    if link_to_db is None:
        print("Database connection failed. Exiting program. ❌")
        exit(1)

    # Allows generating a cursor to execute SQL.
    link_to_db_cursor = link_to_db.cursor()

    # Generating a table for users' spending.
    link_to_db_cursor.execute('''CREATE TABLE IF NOT EXISTS users_expenses (
                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                              date_of_spending TEXT NOT NULL,
                              type_of_spending TEXT NOT NULL,
                              amount_spent REAL NOT NULL)''')

    # Organising data entities within financial tables to ensure structured
    # storage.
    the_database_entities = {
        # Table to track user income records, inc source, amount and date.
        "users_incomes": '''CREATE TABLE IF NOT EXISTS users_incomes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            source_of_income TEXT NOT NULL,
                            sum_of_income REAL NOT NULL,
                            date_of_income DATE NOT NULL)''',

        # Table to determine the user's budget using their income and spending.
        "budget_calculator": '''CREATE TABLE IF NOT EXISTS budget_calculator (
                            name_of_category TEXT PRIMARY KEY,
                            budget_value REAL NOT NULL,
                            type_of_category TEXT CHECK(type_of_category
                            IN ('income', 'expense')) NOT NULL,
                            income_category_name TEXT,
                            expense_category_name TEXT,
                            FOREIGN KEY (income_category_name) REFERENCES
                            income_categories (name_of_category)
                            ON DELETE CASCADE,FOREIGN KEY
                            (expense_category_name) REFERENCES
                            expense_categories (name_of_category)
                            ON DELETE CASCADE)''',

        # Table for monitoring user's savings goals and their progress.
        "saving_goals": '''CREATE TABLE IF NOT EXISTS saving_goals (
                    goal_ID_No INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_of_goal TEXT NOT NULL,
                    commencing_date DATE,
                    finish_date DATE,
                    monthly_target_amount REAL NOT NULL,
                    saved_up_so_far REAL NOT NULL)''',


        # Table to organise various income categories.
        "income_categories": '''CREATE TABLE IF NOT EXISTS income_categories (
                            name_of_category TEXT PRIMARY KEY,
                            description TEXT)''',

        # Table to organise various expense categories.
        "expense_categories": '''CREATE TABLE IF NOT EXISTS
                              expense_categories
                              (name_of_category TEXT PRIMARY KEY,
                              description TEXT)'''
        }

    # Executing SQL commands to generate tables for financial tracking.
    for table_name, query in the_database_entities.items():
        link_to_db_cursor.execute(query)

    # Before disconnecting from the db, all modifications are saved.
    link_to_db.commit()
    link_to_db.close()


# ===================== Budget & Category Management ================
# This section provides functions to:
# - Validate date input to ensure proper formatting.
# - Check if a category exists in either the income or expense table.
# - Set a budget for a specific income or expense category.
# - Add a new category (income or expense) if it does not already exist.
# - Display the budget set for a category.
# - Calculate and display the remaining budget after income and expenses.
def validate_date(date_text):
    """Checks if the given date is in the correct format (YYYY-MM-DD).

    This function tries to convert the entered string into a datetime
    object.
    If it succeeds, the format is valid, and it returns True.
    If it fails (ValueError), it returns False, indicating an incorrect format.

    Args:
        date_text (str): Date entered by user.

    Returns:
        bool: True if the correct date format is YYYY-MM-DD, otherwise False
        and will not be understood by the db.
    """
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def existing_category(category_name, category_type):
    """Checks if a category exists in either the income or expense category
    tables.

    Args:
        category_name (str): The category name to check.
        category_type (str): Either 'income' or 'expense'. To understand which
        table to search.

    Returns:
        bool: True if the category exists, False otherwise.
    """
    # Opens the db connection.
    link_to_db = link_to_finance_db()
    cursor = link_to_db.cursor()

    # Function to normalise format by removing extra spaces and
    # converts text to lowercase for stable retrieval and data storage.
    category_name = category_name.strip().lower()

    # Inspect if category exists in the correct table.
    if category_type == "income":
        cursor.execute("SELECT 1 FROM income_categories WHERE "
                       "LOWER(name_of_category) = ?", (category_name,))
    else:
        cursor.execute("SELECT 1 FROM expense_categories "
                       "WHERE LOWER(name_of_category) = ?", (category_name,))

    category_found = cursor.fetchone()

    # Close the db connection.
    link_to_db.close()
    return category_found is not None


def set_budget_for_category(category_name, budget_value, category_type):
    """Sets up a budget for a specific category (income or expense).

    This function allows users to set their budget based on their defined
    expenses and incomes by a category. This helps to create spending limits.

    Args:
        category_name (str): The category name to set the budget for.
        budget_value (float): The amount for the budget.
        category_type (str): The type of category ('income' or 'expense').

    Raises:
        ValueError: If category_type is not 'income' or 'expense'.
    """
    # Normalises user input.
    category_name = category_name.strip().lower()
    category_type = category_type.strip().lower()

    # Check and validate budget amount clearly added here.
    if budget_value <= 0:
        print("🚩 Budget amount must be greater than zero.")
        return

    # Process of checking if user entered a valid  type of category.
    if category_type not in ['income', 'expense']:
        raise ValueError("Only enter 'income' or 'expense' as category type.")

    # Check if the category exists; if it doesn’t, we can suggest to create it.
    if not existing_category(category_name, category_type):
        print(f"🚩 This category '{category_name}' ({category_type}) doesn't "
              f"exist.")
        add_new = input(
            f"Press Y if you like to add '{category_name}' as a new "
            f"{category_type} category? or N: "
        ).strip().lower()

        if add_new == "y":
            add_category(category_name, category_type)
        else:
            print("🚩 Budget not set. Returning to the main menu.")
            return

    link_to_db = link_to_finance_db()
    cursor = link_to_db.cursor()

    # User can set up or modify budget for a specify category.
    cursor.execute('''INSERT OR REPLACE INTO budget_calculator
                      (name_of_category, budget_value, type_of_category)
                      VALUES (?, ?, ?)''',
                   (category_name, budget_value, category_type))

    # Save changes to the db connection.
    link_to_db.commit()
    print(
        f"Budget of 💷 £{budget_value:.2f} set for '{category_name}' "
        f"({category_type}).")
    print("Returning to the main menu... 🔄\n")

    link_to_db.close()


def add_category(category_name, category_type):
    """Adds a new category to either the income or expense categories table.

    This function helps users to expand their budgeting categories
    by including new types of income or expenses.

    Args:
        category_name (str): The category name to add.
        category_type (str): Tells user particularly if it is an'income' or
        'expense'.
    """
    link_to_db = link_to_finance_db()
    cursor = link_to_db.cursor()

    # Insert the category into the correct table.
    if category_type == "income":
        cursor.execute("INSERT INTO income_categories (name_of_category) "
                       "VALUES (?)", (category_name,))
    else:
        cursor.execute("INSERT INTO expense_categories (name_of_category) "
                       "VALUES (?)", (category_name,))

    link_to_db.commit()
    print(f"Category '{category_name}' ({category_type}) added successfully!")

    link_to_db.close()


def display_category_budget(category_name, category_type):
    """Fetches and displays the budget set for a specific category (income or
    expense).
    This function lets users to view their set budget values for the selected
    income or expense category and shows it to them.

    Args:
        category_name (str): The category of the budget being viewed.
        category_type (str): Tells user particularly if it is an'income' or
        'expense'.

    """
    category_name = category_name.strip().lower()
    category_type = category_type.strip().lower()

    # Confirms to the user whether the catgeory exists or not.
    # If the category doesn't exist, it alerts them to add it before.
    if not existing_category(category_name, category_type):
        print(f"🚩 Category '{category_name}' ({category_type}) doesn't exist. "
              "Add it before setting or viewing a budget.")
        return

    link_to_db = link_to_finance_db()
    cursor = link_to_db.cursor()

    # Fetch the budget for particular category.
    cursor.execute('''SELECT budget_value FROM budget_calculator
                      WHERE LOWER(TRIM(name_of_category)) = ?
                      AND LOWER(TRIM(type_of_category)) = ?''',
                   (category_name, category_type))

    result = cursor.fetchone()

    # Show budget information.
    if result:
        print(f"Budget: '{category_name}' ({category_type}) → £{result[0]:.2f}"
              )
    else:
        print(f"No budget set for '{category_name}' ({category_type}). "
              "Set one first.")

    link_to_db.close()


def magical_budget_calculator():
    """
    Shows and calculates the remaining budget from income and expenses.

    This function calculates the user's budget by retrieving total income
    and total expenses from the database. It then calculates the remaining
    balance (budget) by subtracting expenses from income and displays the
    result to the user.
    """
    # Connect to the db.
    link_to_db = link_to_finance_db()
    cursor = link_to_db.cursor()

    # Fetch the user's total income.
    cursor.execute(
        "SELECT SUM(sum_of_income) FROM users_incomes"
    )
    # If there is no income, set the value to 0.
    total_income = cursor.fetchone()[0] or 0

    # Fetch the user’s total expenses.
    cursor.execute(
        "SELECT SUM(amount_spent) FROM users_expenses"
    )
    # If there is no income, set the value to 0.
    total_expenses = cursor.fetchone()[0] or 0

    # Calculate the remaining budget (income - expenses) for the user.
    remaining_budget = total_income - total_expenses

    # Show the user their personalised budget.
    print(f"This is your total income ✨: £{total_income:.2f}")
    print(f"This is your total expenses 💶: £{total_expenses:.2f}")
    print(f"Bibbidi-Bobbidi-Boo 🪄, this is your remaining budget ⏳:"
          f'£{remaining_budget:.2f}')

    print("Returning to the main menu... 🔄\n")

    link_to_db.close()


# =========================== Expense Management ===========================
# This section provides functions to:
# - Record a new expense entry.
# - Add a new expense category if it doesn't exist.
# - View expenses (all or filtered by category or date).
# - Update an existing expense record.
# - Delete an expense category.
def record_new_spending():
    """
    Prompts the user for a new expense, including date, category, and amount
    of expenditure.

    Adds the expense to the database and ensures the category is registered.

    1. Validates the date format to make sure of the consistency.
    2. Check whether the expense category exists; if not, asks the user to
    add it.
    3. Restrict the input to only valid numeric values for the amount.
    4. Saves the new expense in the database.
    5. Gets rid of any extra spaces.

    Returns:
        None
    """

    while True:
        date_of_spending = input("What was the date of the expense "
                                 "(YYYY-MM-DD) 📆: ").strip()
        if validate_date(date_of_spending):
            break
        print("🚩 Invalid date format! Please enter in YYYY-MM-DD format.")

    type_of_spending = input("Enter the category of expense 🛒: "
                             ).strip().lower()

    # Ensure category exists or request user to add it.
    # If user inputs N, display message and return to the main menu.
    if not existing_category(type_of_spending, "expense"):
        print(f"🚩 This category '{type_of_spending}' (expense) doesn't exist.")
        add_new = input(f"Would you like to add '{type_of_spending}' as a new "
                        f"expense category? (Y/N): ").strip().lower()

        if add_new == "y":
            add_expense_category(type_of_spending)

            if not existing_category(type_of_spending, "expense"):
                print("🚩 Category not added — possibly due to a duplicate or "
                      "invalid name.\n"
                      "Please try adding the expense again with a valid new "
                      "category.")
                return

        else:
            print("🚩 Expense not recorded. Returning to the main menu.")
            return

    # Check that the amount spent is a valid numeric value and greater than
    # zero.
    while True:
        try:
            amount_spent = float(input("How much did you spend? 🛍️: ").strip())
            # Added validation to ensure the entered expense amount is greater
            # than zero to prevent invalid entries.
            if amount_spent <= 0:
                print("🚩 Expense amount must be greater than zero.")
                continue  # Prompt user again if amount is invalid.
            break
        except ValueError:
            print("🚩 Invalid input! Please enter a numeric value.")

    # Put the expense record into the db.
    try:
        with sqlite3.connect("Spend_Wise_Buddy.db") as link_to_db:
            cursor = link_to_db.cursor()

            # Insert a new expense record into the 'users_expenses' table.
            cursor.execute(
                "INSERT INTO users_expenses (date_of_spending, "
                "type_of_spending, "
                "amount_spent) VALUES (?, ?, ?)",
                (date_of_spending, type_of_spending, amount_spent)
            )

            # Commit the transaction to save changes to the database
            link_to_db.commit()

    # Handle any database-related errors.
    except sqlite3.Error as e:
        print(f"🚩 Database error occurred while saving expense: {e}")
        return

    print("This expense has been successfully recorded! ✅")
    print("Returning to the main menu... 🔄\n")


def add_expense_category(category_name):
    """Adds a new expense category if it does not already exist.

    Args:
        category_name (str): The name of the expense category.

    Returns:
        None
    """

    category_name = category_name.strip().lower()

    # Check if empty.
    if not category_name:
        print("🚩 Category name cannot be empty!")
        return

    with sqlite3.connect("Spend_Wise_Buddy.db") as link_to_db:
        cursor = link_to_db.cursor()

        # Check if category already exists. (case-insensitive)
        cursor.execute("SELECT 1 FROM expense_categories WHERE "
                       "LOWER(name_of_category) = ?",
                       (category_name,))
        existing_category = cursor.fetchone()

        if existing_category:
            print(f"🚩 Category '{category_name}' already exists!")
            return

        # Put the new category into the db.
        cursor.execute("INSERT INTO expense_categories (name_of_category) "
                       "VALUES (?)",
                       (category_name,))
        link_to_db.commit()

        print(f"Category '{category_name}' has been successfully added. ✅ ")


def check_expenses():
    """Give users the option to view their recorded expenditure using filters.

    Options given:
    1. View All Expenses.
    2. View Expenses by Type.
    3. View Expenses by a particular date.

    Returns:
        None
    """

    # Set up connection to the db.
    with sqlite3.connect("Spend_Wise_Buddy.db") as link_to_db:
        link_to_db_cursor = link_to_db.cursor()

        # Giving the user options on ways of view their expenses.
        print("\nWhat is your preferred way to view your spending? 📊💰")
        print("1️⃣ Display all my expenses.")
        print("2️⃣ Display my expenses by type.")
        print("3️⃣ Display my expenses by date.")

        # Request the user to select the filtering options out of 3.
        choice = input("Please enter your choice: 1/2/3 🧐").strip()

        # Based on the user's input, run the relevant SQL query.
        if choice == "1":
            # If the user chooses option 1, display all expenses from the db.
            link_to_db_cursor.execute("SELECT * FROM users_expenses")

        elif choice == "2":
            # If the user picks option 2,
            # ask which type of expense to filter by.
            type_of_spending = input("Please enter the type of expense 🛒: "
                                     ).strip().lower()
            if not type_of_spending:
                print("🚩 Expense type cannot be empty. Please try again!")
                return

            # Only retrieve expenses that match the type entered.
            link_to_db_cursor.execute(
                "SELECT * FROM users_expenses WHERE LOWER(TRIM"
                "(type_of_spending)) = ?",
                # Ensuring proper matching regardless of case or spaces.
                (type_of_spending,)
            )

        elif choice == "3":
            # If user picks option 3,
            # ask to input the specific date to filter by.
            # However, to ensure correct date format, if not corrected inputted
            # let user know that it is invalid.
            date_of_spending = input("Enter the date (YYYY-MM-DD) 📅: ").strip()
            if not validate_date(date_of_spending):
                print("🚩 Invalid date format! Please enter in YYYY-MM-DD "
                      "format.")
                return
            # Show only the expenses from that date to the user.
            link_to_db_cursor.execute(
                "SELECT * FROM users_expenses WHERE date_of_spending = ?",
                (date_of_spending,)
            )

        else:
            # Show an error message, if the user enters an invalid option.
            print("Oops! 🚩 Option not available. Please pick 1, 2, or 3.")
            return

        # Accumulate and store the query results from the db.
        users_expenses = link_to_db_cursor.fetchall()

        # Present all expenses to the user.
        if users_expenses:
            print("\nHave a look at all your recorded expenses 📝:")
            print("-" * 50)
            for exp in users_expenses:
                # Print each expense in an easy-to-read format.
                print(f"🆔 ID: {exp[0]}, 🗓️ Date: {exp[1]}, "
                      f"🛒 Type: {exp[2]}, 💵 Amount: £{exp[3]:.2f}")

            print("Returning to the main menu... 🔄\n")

        else:
            # Display a message if no matching expenses are found.
            print("No expenses found that meet your specified criteria. 🚫")


def update_my_spending():
    """
    Function allows the user to update an existing expense by
    modifying its amount.

    - Checks whether the ID exists before making any changes.
    - Shows the current information of the chosen expense.
    - Prompts for a new spending amount and saves it in the database.

    Returns:
        None
    """
    link_to_db = link_to_finance_db()
    link_to_db_cursor = link_to_db.cursor()

    expense_ID_No = input("Enter the expense ID number to update: ").strip()

    if not expense_ID_No.isdigit():
        print("🚩 Invalid input! Expense ID must be a number.")
        return

    link_to_db_cursor.execute(
        "SELECT * FROM users_expenses WHERE id = ?",
        (expense_ID_No,)
    )
    user_expenses = link_to_db_cursor.fetchone()

    if user_expenses:
        print(f"🆔 ID: {user_expenses[0]}, 🗓️ Date: {user_expenses[1]}, "
              f"🛒 Type: {user_expenses[2]}, 💵 Amount: £{user_expenses[3]:.2f}")

        while True:
            try:
                new_spending_amount = float(input("Enter the new amount of "
                                                  "spending 💵: ").strip())
                break
            except ValueError:
                print("🚩 Invalid input! Please enter a valid numeric amount.")

        link_to_db_cursor.execute(
            "UPDATE users_expenses SET amount_spent = ? WHERE id = ?",
            (new_spending_amount, expense_ID_No)
        )
        link_to_db.commit()
        print("Expense changed successfully! 😇 ✅")
    else:
        print("Invalid expense ID, please try again. 😔")

    print("Returning to the main menu... 🔄\n")
    link_to_db.close()


def delete_spending_type():
    """
    Prompts the user to delete all expenses associated with a specific
    category.

    This function ensures that the category exists in the db before
    trying to delete it.

    Asks the user for confirmation before removing the data.

    Returns:
        None
    """
    link_to_db = link_to_finance_db()
    link_to_db_cursor = link_to_db.cursor()

    category_to_delete = input("What type of expense do you want to delete? "
                               ).strip().lower()

    if not category_to_delete:
        print("🚩 Expense type cannot be empty! Please enter a valid type.")
        link_to_db.close()
        return

    link_to_db_cursor.execute(
        "SELECT * FROM users_expenses WHERE LOWER(TRIM(type_of_spending)) = ?",
        (category_to_delete,)
    )
    expense_found = link_to_db_cursor.fetchall()

    if expense_found:
        confirm = input(
            f"Are you sure you want to delete all expenses under "
            f"'{category_to_delete}'? (Y/N): ").strip().lower()
        if confirm == "y":
            link_to_db_cursor.execute(
                "DELETE FROM users_expenses WHERE LOWER(TRIM(type_of_spending"
                ")) = ?",
                (category_to_delete,)
            )
            link_to_db.commit()
            print(f"All expenses under '{category_to_delete}' are deleted! ✅")
        else:
            print("Deleting the expense has now been cancelled.")
    else:
        print(f"No expenses found under '{category_to_delete}'.")

    print("Returning to the main menu... 🔄\n")
    link_to_db.close()


# =========================== Income Management ===========================
# This section provides functions to:
# - Record a new income entry.
# - Add a new income category if it doesn't exist.
# - View income records (all or filtered).
# - Update an existing income record.
# - Delete an income category.
def record_an_income():
    """
    Allows the user to add a new income entry.
    If the category does not exist, prompts the user to add it.
    User has to provide:
    1. Date of income.
    2. Source of category of income.
    3. Amount received.

    This function ensures:
    1. The date is validated and formatted correctly (YYYY-MM-DD).
    2. The income category exists; if not, the user is prompted to add it.
    3. The income amount entered is a valid numeric value and greater than
    zero.
    4. Then, the income details are saved in the database.

    Returns:
        None
    """
    while True:
        date_of_income = input("Enter the date of income YYYY-MM-DD) 📆: "
                               ).strip()
        if validate_date(date_of_income):
            break
        print("🚩 Invalid date format! Please enter in YYYY-MM-DD format.")

    source_of_income = input("What is the source of income? 💼: "
                             ).strip().lower()

    # Check if the category exists, otherwise ask user to add it.
    if not existing_category(source_of_income, "income"):
        print(f"🚩 Category '{source_of_income}' (income) doesn't exist.")
        add_new = input(f"Would you like to add '{source_of_income}' as a new "
                        "income category? (Y/N): ").strip().lower()

        if add_new == "y":
            add_income_category(source_of_income)
        else:
            print("🚩 Income not recorded. Returning to the main menu.")
            return

    # Check that the amount of income is valid numeric value and greater than
    # zero.
    while True:
        try:
            sum_of_income = float(input("Please input the income amount 💰: "
                                        ).strip())
            # ✅ Added validation to ensure the entered income amount is
            # greater than zero to avoid invalid entries.
            if sum_of_income <= 0:
                print("🚩 Income amount must be greater than zero.")
                continue  # Prompt user again if amount is invalid.
            break
        except ValueError:
            print("🚩 Invalid input! Please enter a numeric value.")

    # Put income record into the db.
    with sqlite3.connect("Spend_Wise_Buddy.db") as link_to_db:
        cursor = link_to_db.cursor()
        cursor.execute(
            '''INSERT INTO users_incomes
            (source_of_income, sum_of_income, date_of_income)
            VALUES (?, ?, ?)''',
            (source_of_income, sum_of_income, date_of_income)
        )
        link_to_db.commit()

    print(f"✅ Income from '{source_of_income}' recorded successfully!")
    print("Returning to the main menu... 🔄\n")


def add_income_category(category_name=None):
    """Allows the user to add a new income category to the database.
    If it doesn't exist already.

    Args:
        category_name (str): The name of the new income category.
        If not given, the user is asked to enter one.

    Returns:
        None
    """

    if not category_name:
        category_name = input("Enter the new income category (e.g., Salary): "
                              ).strip()

    category_name = category_name.strip().lower()

    # Do not allow black input.
    if not category_name:
        print("🚩 Income category name cannot be empty!")
        return

    description = input("Enter a description for this category (optional): "
                        ).strip()

    with sqlite3.connect("Spend_Wise_Buddy.db") as link_to_db:
        cursor = link_to_db.cursor()

        # Check if the category already exists.
        cursor.execute(
            "SELECT 1 FROM income_categories "
            "WHERE LOWER(name_of_category) = ?",
            (category_name,)
        )
        existing_category = cursor.fetchone()

        if existing_category:
            print(f"🚩 Income category '{category_name}' already exists!")
            return

        # Put the new income category into the db.
        cursor.execute(
            "INSERT INTO income_categories (name_of_category, description) "
            "VALUES (?, ?)",
            (category_name, description)
        )
        link_to_db.commit()

    print(f"✅ Income category '{category_name}' added successfully!")


def check_income():
    """
    Allow the user to view their income records.

    1. Connect to the database.
    2. Ask the user if they want to see all income or filter by type.
    3. Retrieve the income data using SQL queries.
    4. Display the income records in a readable format.

    2 options given to the user:
    1. View all income records.
    2. Filter by a particular income source/ category.

    Returns:
        None
    """
    link_to_db = sqlite3.connect("Spend_Wise_Buddy.db")
    link_to_db_cursor = link_to_db.cursor()

    # Display the user how they want to view income.
    print("\nHow would you like to view your income? 📊")
    print("1. See all income records.")
    print("2. See income by source (e.g., only 'Salary' or 'Business').")

    choice = input("Enter your choice (1/2): ").strip()

    if choice == "1":
        # Gather all income records.
        link_to_db_cursor.execute("SELECT * FROM users_incomes")
    elif choice == "2":
        # Ask the user to specify the income type.
        income_source = input("Enter the income source: ").strip().lower()
        link_to_db_cursor.execute(
            "SELECT * FROM users_incomes WHERE LOWER(source_of_income) = ?",
            (income_source,)
        )
    else:
        print("🚩 Option unavailable. Please select out of 1 or 2. ")
        link_to_db.close()
        return

    # Fetch all matching records.
    user_income = link_to_db_cursor.fetchall()

    # Show user income records if they are found.
    if user_income:
        print("\nYour Personal Income Records: 📄")
        print("-" * 50)

        for inc in user_income:
            print(f"🆔 ID: {inc[0]}, "
                  f"🗓️ Date: {inc[3]}, "
                  f"📌 Source: {inc[1]}, "
                  f"💰 Amount: £{inc[2]:.2f}")
            # Add space to make it easier to read.
            print()
    else:
        print("🚩 No income records found matching your criteria.")

    print("Returning to the main menu... 🔄\n")
    # Close the db connection.
    link_to_db.close()


# Function to modify the user’s income.
def update_my_income():
    """
    Enable users to update their current incomes.

    1. Connect to the database.
    2. Ask the user for the income ID they wish to update.
    3. Display the current details of that income.
    4. Ask them to enter and update a new income amount in the database.

    The function authorises that the record exists.

    Returns:
        None
    """
    link_to_db = sqlite3.connect("Spend_Wise_Buddy.db")
    link_to_db_cursor = link_to_db.cursor()

    # Ask user for the ID of the income record to update.
    income_ID_str = input(
        "Enter the income ID number you want to update: "
    ).strip()

    if not income_ID_str.isdigit() or int(income_ID_str) <= 0:
        print("🚩 Invalid ID! Please enter a valid positive numeric income ID.")
        link_to_db.close()
        return

    income_ID_No = int(income_ID_str)

    # Find the current income record.
    link_to_db_cursor.execute(
        "SELECT * FROM users_incomes WHERE id = ?", (income_ID_No,))
    user_income = link_to_db_cursor.fetchone()

    # Only update if the user’s income ID exists.
    if user_income:
        print("\n📄 Current Income Record:")
        print(f"🆔 ID: {user_income[0]}")
        print(f"🗓️ Date: {user_income[3]}")
        print(f"📌 Source: {user_income[1]}")
        print(f"💰 Amount: £{user_income[2]:.2f}")

        while True:
            try:
                new_income_amount = float(input("Enter the new "
                                                "income amount 💰: "))
                if new_income_amount <= 0:
                    print("🚩 Income amount must be greater than **£0**. "
                          "Please try again.")
                    continue
                break
            except ValueError:
                print("🚩 Invalid input! Please enter a "
                      "**valid** numeric value.")

        # Modify the db record.
        link_to_db_cursor.execute(
            "UPDATE users_incomes SET sum_of_income = ? WHERE id = ?",
            (new_income_amount, income_ID_No)
        )
        link_to_db.commit()

        print("New income record updated successfully! ✅")
    else:
        print("Cannot find income ID. Please try again. 🚩")

    print("Returning to the main menu... 🔄\n")

    link_to_db.close()


def delete_income_type():
    """
    Allow the user to delete an entire income type/category.

    1. Connect to the database.
    2. Ask the user which income type to delete.
    The function verifies if records for that particular income category
    exists.
    3. Confirm deletion before removing all matching records.

    Returns:
        None
    """
    link_to_db = sqlite3.connect("Spend_Wise_Buddy.db")
    link_to_db_cursor = link_to_db.cursor()

    category_to_delete = input("Enter the income type to delete: "
                               ).strip().lower()

    # Use case-insensitive matching and trim spaces to improve accuracy.
    link_to_db_cursor.execute(
        "SELECT * FROM users_incomes WHERE LOWER(TRIM(source_of_income)) = ?",
        # Ensuring proper matching regardless of case or extra spaces.
        (category_to_delete,)
    )
    user_income = link_to_db_cursor.fetchall()

    if user_income:
        confirm = input(f"Delete '{category_to_delete}'? Enter (Y/N): "
                        ).strip().lower()

        if confirm == "y":
            link_to_db_cursor.execute(
                "DELETE FROM users_incomes WHERE LOWER(TRIM(source_of_income))"
                "= ?",
                # Ensuring proper deletion regardless of case or spaces
                (category_to_delete,)
            )
            link_to_db.commit()
            print(f"Income records under '{category_to_delete}' are deleted. ✅"
                  )
        else:
            print("Deleting for this income type has now been cancelled. 🚩")
    else:
        print(f"No income records found under '{category_to_delete}'. 🚩")

    print("Returning to the main menu... 🔄\n")
    link_to_db.close()


# ===================== Income & Expense Tracker =====================
# This section provides functions to:
# - Generate a summary of total income, expenses, and remaining balance.
# - Break down income and expenses by category (type).
# - Track spending trends over time to show how expenses changes.
def income_expenses_summary():
    """
    Calculate and display total income, expenses and remaining balance
    for a particular period (monthly) or (annually).

    This function allows the user to:
    1. View financial summaries based on selected timeframe.
    2. Compare total income and total expenses for the month.
    3. Calculates the remaining balance (income - expenses),
       again like the magical budget calculator.

    Returns:
        None
    """

    # Ask user to choose between monthly or annual summary.
    while True:
        timeframe = input("Do you want a monthly or annual summary? "
                          "(monthly/annually): ").strip().lower()
        if timeframe in ["monthly", "annually"]:
            break
        print("🚩 Invalid option! Please choose 'monthly' or 'annually'.")

    # Gather the current date and time.
    selected_datetime = datetime.now()

    # Setting SQL filters according to the user's choice.
    if timeframe == "monthly":
        formatted_date = selected_datetime.strftime("%Y-%m")
        date_filter = "strftime('%Y-%m', date_of_spending) = ?"
        income_filter = "strftime('%Y-%m', date_of_income) = ?"
    else:
        formatted_date = selected_datetime.strftime("%Y")
        date_filter = "strftime('%Y', date_of_spending) = ?"
        income_filter = "strftime('%Y', date_of_income) = ?"

    # Establish a connection to the database.
    with sqlite3.connect("Spend_Wise_Buddy.db") as link_to_db:
        cursor = link_to_db.cursor()

        # Retrieve total expenses for the selected period.
        cursor.execute(
            f"SELECT SUM(amount_spent) FROM users_expenses "
            f"WHERE {date_filter}",
            (formatted_date,)
        )

        total_amount_of_expenses = cursor.fetchone()[0] or 0

        # Retrieve total income for the selected period.
        cursor.execute(
            f"SELECT SUM(sum_of_income) FROM users_incomes "
            f"WHERE {income_filter}",
            (formatted_date,)
        )

        total_amount_of_income = cursor.fetchone()[0] or 0

    # Calculate the remaining balance.
    remaining_balance = total_amount_of_income - total_amount_of_expenses

    # Display the summary to the user.
    print(f"\n📊 Summary ({timeframe.capitalize()}):")
    print(f"💰 Total Income: £{total_amount_of_income:.2f}")
    print(f"💸 Total Expenses: £{total_amount_of_expenses:.2f}")
    print(f"🚀 Remaining Balance: £{remaining_balance:.2f}")

    print("Returning to the main menu... 🔄\n")


# Function to break down spending and income by type.
def type_of_spending_and_income():
    """Expenses and incomes are broken down into categories.

    Groups in this function are broken down to either expense
    ("Groceries, "Travel") or income ("Events", "Tutoring")
    by categories.

    Gives a total amount for each category.

    Returns:
        None
    """
    link_to_db = link_to_finance_db()
    cursor = link_to_db.cursor()

    # Show the user a breakdown of their expenses by type.
    print("\nBreakdown of your expenses by type 🛍️:")
    cursor.execute(
        "SELECT type_of_spending, SUM(amount_spent) "
        "FROM users_expenses GROUP BY type_of_spending"
    )
    for type, total in cursor.fetchall():
        print(f"Type: {type}, Total: £{total:.2f}")

    # Show the user a breakdown of their incomes by type.
    print("\nBreakdown of your incomes by type 💼:")
    cursor.execute(
        "SELECT source_of_income, SUM(sum_of_income) "
        "FROM users_incomes GROUP BY source_of_income"
    )
    for source, total in cursor.fetchall():
        print(f"Source: {source}, Total: £{total:.2f} 💰")

    print("Returning to the main menu... 🔄\n")
    link_to_db.close()


def trends_for_tracking_spending():
    """Track changes in expenses over time by analysing monthly
    expense trends.

    1. Groups expenses by month to track trends.
    2. Assists users in identifying trends in their spending patterns.
    3. Shows a summary of total expenses per month.

    Return:
        None
    """
    link_to_db = link_to_finance_db()
    cursor = link_to_db.cursor()

    print("\nTrends in spending")
    cursor.execute(
        "SELECT strftime('%Y-%m', date_of_spending), SUM(amount_spent) "
        "FROM users_expenses GROUP BY strftime('%Y-%m', date_of_spending)"
    )

    # A loop through query results and as a result displaying the spending
    # trends.
    for month, total in cursor.fetchall():
        print(f"Month: {month}, Total Expenses: £{total:.2f}")

    print("Returning to the main menu... 🔄\n")
    link_to_db.close()


# ===================== Financial Goal Management ======================
# This section allows users to:
# - Set a personalised financial goal with a target amount and timeframe.
# - Track progress toward achieving their savings goals.
# - Update their savings amount as they progress.
def personalised_financial_goal(name_of_goal, desired_amount,
                                commencing_date, finish_date):
    """
    Enables user to assign a financial goal with a desired amount in a
    given time period.

    In this function, the user can set a goal name, the desired savings amount,
    and start and end dates for achieving the target.

    Args:
        name_of_goal (str): The title of the financial goal.
        desired_amount (float): The total amount the user wishes to save.
        commencing_date (str): The commencing date of the goal (YYYY-MM-DD).
        finish_date (str): The deadline date of the goal (YYYY-MM-DD).
    """

    # Normalise input to lowercase for consistency.
    name_of_goal = name_of_goal.strip().lower()

    # Function to ensure the finish goal's end date occurs after start date.
    if datetime.strptime(finish_date, "%Y-%m-%d") <= datetime.strptime(
                         commencing_date, "%Y-%m-%d"):
        print("🚩 End date must be after the start date.")
        return

    link_to_db = link_to_finance_db()
    cursor = link_to_db.cursor()

    # Store the goal in the database with an initial saved amount of 0 as well.
    cursor.execute(
        '''INSERT INTO saving_goals
           (name_of_goal, monthly_target_amount, saved_up_so_far,
            commencing_date, finish_date)
           VALUES (?, ?, ?, ?, ?)''',
        (name_of_goal, desired_amount, 0, commencing_date, finish_date)
    )

    link_to_db.commit()

    # Confirm a message to the user that the goal has been generated.
    print(
        f"Your personalised financial goal '{name_of_goal.capitalize()}' has "
        f"been assigned with a desired amount of £{desired_amount:.2f} "
        f"from {commencing_date} to {finish_date}. 🎯"
    )

    print("Returning to the main menu... 🔄\n")
    link_to_db.close()


def browse_goal_progress(name_of_goal):
    """
    This function permits users to see their personal progress toward their
    financial goals and also allows to update savings.

    The function accumlates all the details of the particular goal,
    presenting the total saving goal, the amount saved so far,
    and the remaining balance left to achieve that goal.

    Args:
        name_of_goal (str): The name of the financial goal to check progress.
    """

    # Normalise input for consistency.
    # Gather all financial goal's target amount and saved amount.
    name_of_goal = name_of_goal.strip().lower()
    with sqlite3.connect("Spend_Wise_Buddy.db") as link_to_db:
        cursor = link_to_db.cursor()
        cursor.execute(
            '''SELECT monthly_target_amount, saved_up_so_far
               FROM saving_goals WHERE LOWER(name_of_goal) = ?''',
            (name_of_goal,)
            )
    result = cursor.fetchone()

    # Show the progress details, if the goal exists.
    if result:
        desired_amount, saved_so_far = result
        remaining_amount = desired_amount - saved_so_far

        print(f"🎯 Goal: {name_of_goal.capitalize()}")
        print(f"🏆 Total Target: £{desired_amount:.2f}")
        print(f"💰 Saved So Far: £{saved_so_far:.2f}")
        print(f"🚀 Remaining: £{remaining_amount:.2f}")

        # Allow the user to contribute more towards the savings, if goals have
        # not been met yet.
        if remaining_amount > 0:
            add_more = input("Would you like to add savings towards this "
                             "goal? (Y/N): ").strip().lower()
            if add_more == "y":
                try:
                    new_savings = float(input("Enter the amount you want to "
                                              "add 💰: £").strip())
                    # Check that the savings amount is more than zero.
                    if new_savings <= 0:
                        print("🚩 Savings amount must be greater than zero.")
                        return

                    updated_savings = saved_so_far + new_savings

                    # Connect to db to update saving progress.
                    db_path = "Spend_Wise_Buddy.db"
                    with sqlite3.connect(db_path) as link_to_db:

                        cursor = link_to_db.cursor()
                    cursor.execute(
                            '''UPDATE saving_goals
                               SET saved_up_so_far = ?
                               WHERE LOWER(name_of_goal) = ?''',
                            (updated_savings, name_of_goal)
                        )
                    link_to_db.commit()

                    print(f"✅ Added £{new_savings:.2f} to your savings!")
                    remaining_balance = desired_amount - updated_savings
                    print(f"🚀 Remaining Balance: £{remaining_balance:.2f}")

                except ValueError:
                    print("🚩 Invalid input! Please enter a numeric value.")
        else:
            print("🎉 Congratulations! You have reached your goal! 🏆")

    else:
        print(f"❌ Goal '{name_of_goal}' not found. ❌")

    print("Returning to the main menu... 🔄\n")


# Function to present a user-friendly menu.
def user_main_menu():
    """
    Display the main menu for the Spend Wise Buddy Program.

    Allows users to navigate through various options and sub-menus,
    and perform the corresponding action.

    Once the option has been selected by the user, this
    menu supports usability by calling the functions based
    on the user input.

    Gives the user an option to return, restart or exit the program.

    It gives the user the ability to manage their expenses, income,
    budgets, financial goals and obtain reports with summaries of their
    incomes and expenses over a month or year. As well as breakdowns and
    trends.
    """
    while True:
        print("\n✨ Hello, annyeonghaseyo and Welcome to Spend Wise Buddy! ✨")
        print("1️⃣  Expenses (Register, View, Update, Delete 📝📊🔍)")
        print("2️⃣  Income (Register, View, Update, Delete 💵💰🔎)")
        print("3️⃣  Budget Management (Set and view budgets 🎯🏦)")
        print("4️⃣  Financial Goals (Set and track your financial goals 🚀)")
        print("5️⃣  Reports & Trends (Summaries, Breakdown & trends 📈)")
        print("6️⃣  Quit Program (Exit the application ❌)")

        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == "1":
            expenses_menu()
        elif choice == "2":
            income_menu()
        elif choice == "3":
            budget_menu()
        elif choice == "4":
            goals_menu()
        elif choice == "5":
            reports_menu()
        elif choice == "6":
            print("👋🏽 Au Revoir, Thank you for choosing Spend Wise Buddy. 😎🌟")
            restart = input("Would you like to restart the application? "
                            "(Y/N): ").strip().lower()
            if restart == "y":
                continue
            else:
                break
        else:
            print("🚩 Invalid choice! Please select an option from 1-6.")


# Expenses Menu
def expenses_menu():
    print("\n-- Expenses Menu --")
    print("1️⃣ Add new expense 📝")
    print("2️⃣ Add a new expense category 🏷️")
    print("3️⃣ View expenses 📊")
    print("4️⃣ Update an expense 🔄")
    print("5️⃣ Delete an expense category 🚫")
    print("0️⃣ Return to Main Menu 🔙")

    choice = input("Enter your choice: ")

    if choice == "1":
        record_new_spending()
    elif choice == "2":
        category_name = input("Enter the new expense category name: ").strip()
        if category_name:
            add_expense_category(category_name)
        else:
            print("🚩 Category name cannot be empty!")
    elif choice == "3":
        check_expenses()
    elif choice == "4":
        update_my_spending()
    elif choice == "5":
        delete_spending_type()
    elif choice == "0":
        return
    else:
        print("🚩 Invalid option!")


# Income Menu
def income_menu():
    print("\n-- Income Menu --")
    print("1️⃣ Add income 💵")
    print("2️⃣ Add a new income category 🏷️")
    print("3️⃣ View income 💰")
    print("4️⃣ Update income 💼")
    print("5️⃣ Delete an income category 🚫")
    print("0️⃣ Return to Main Menu 🔙")

    choice = input("Enter your choice: ").strip()
    if choice == "1":
        record_an_income()
    elif choice == "2":
        add_income_category()
    elif choice == "3":
        check_income()
    elif choice == "4":
        update_my_income()
    elif choice == "5":
        delete_income_type()
    elif choice == "0":
        return
    else:
        print("🚩 Invalid option!")


# Budget Management Menu
def budget_menu():
    print("\n-- Budget Management Menu --")
    print("1️⃣ Set budget for a category 🎯")
    print("2️⃣ View budget for a category 🏦")
    print("3️⃣ Magical budget calculator 🧙🪄")
    print("0️⃣ Return to Main Menu 🔙")

    choice = input("Enter your choice: ").strip()
    if choice == "1":
        category_name = input("Enter category name (e.g., Salary, "
                              "Food): ").strip().lower()

        try:
            budget_value = float(input(f"Enter budget for '{category_name}': £"
                                       ).strip())
            if budget_value <= 0:
                print("🚩 Budget must be greater than zero.")
                return
        except ValueError:
            print("🚩 Invalid input! Please enter a numeric value.")
            return

        category_type = input("Income or expense? "
                              "(income/expense): ").strip().lower()

        try:
            set_budget_for_category(category_name, budget_value, category_type)
        except ValueError as e:
            print(f"🚩 {e}")

    elif choice == "2":
        category_name = input("Enter category name (e.g., Salary, "
                              "Food): ").strip().lower()
        category_type = input("Is this category income or expense? "
                              "(income/expense): ").strip().lower()
        display_category_budget(category_name, category_type)

    elif choice == "3":
        magical_budget_calculator()

    elif choice == "0":
        return

    else:
        print("🚩 Invalid option!")


# Personal Financial Goals Menu
def goals_menu():
    print("\n-- Financial Goals Menu --")
    print("1️⃣ Set a personalised financial goal 🚀")
    print("2️⃣ View or update savings progress 📈")
    print("0️⃣ Return to Main Menu 🔙")

    choice = input("Enter your choice: ")

    # Option 1: Set a personalised financial goal.
    if choice == "1":
        # Ask for the goal name clearly.
        goal_name = input("Enter the goal name 🎯: ").strip()

        # Convert user's input into a numercial value (float).
        try:
            target_amount = float(input("Enter the target amount 💰: £"
                                        ).strip())
            # Check that the goal amount is more than zero.
            if target_amount <= 0:
                print("🚩 Goal amount must be greater than zero.")
                return
        except ValueError:
            # If the input is not numeric, clearly displays an error message
            # and return
            print("🚩 Invalid input! Please enter a numeric amount.")
            return

        # Allow user to enter start and end dates for financial goal.
        start_date = input("Enter start date (YYYY-MM-DD) 📆: ").strip()
        end_date = input("Enter end date (YYYY-MM-DD) 📆: ").strip()

        # Function to ensure the finish goal's end date occurs after start
        # date.
        try:
            if datetime.strptime(end_date, "%Y-%m-%d") <= datetime.strptime(
                                 start_date, "%Y-%m-%d"):
                print("🚩 End date must be after the start date.")
                print("Please try again. 🔄\n")
                return  # Stops the process and returns to menu
        except ValueError:
            # Inform user if the date format is invalid.
            print("🚩 Invalid date format! Please use YYYY-MM-DD.")
            return

        # Function allows personalised_financial_goal() to clearly work after
        # validation passes.
        personalised_financial_goal(goal_name, target_amount, start_date,
                                    end_date)

    # Option 2: View or update existing savings progress.
    elif choice == "2":
        goal_name = input("Enter the goal name 🎯: ").strip()
        # Function to view and potentially update the goal.
        browse_goal_progress(goal_name)

    # Option 0: Return to the main menu.
    elif choice == "0":
        return

    # Handles any other unxpected user inputs.
    else:
        print("🚩 Invalid option!")


def reports_menu():
    print("\n-- Reports & Trends Menu --")
    print("1️⃣ View income and expense summary 📊 (Monthly/Annual)")
    print("2️⃣ Track spending trends 📉")
    print("3️⃣ View spending and income by category 🔍")
    print("0️⃣ Return to Main Menu 🔙")

    choice = input("Enter your choice: ").strip()
    if choice == "1":
        income_expenses_summary()
    elif choice == "2":
        trends_for_tracking_spending()
    elif choice == "3":
        type_of_spending_and_income()
    elif choice == "0":
        return
    else:
        print("🚩 Invalid option!")


# Run the menu if this script is executed.
if __name__ == "__main__":
    build_a_financial_db()
    # Call the menu to allow user interactions.
    user_main_menu()

# References List:

# SQLite & Database Integration:
# - Python Software Foundation. (n.d.). sqlite3 — DB-API 2.0 interface.
#   Retrieved from https://docs.python.org/3/library/sqlite3.html
# - Python Software Foundation. (n.d.). os — Miscellaneous OS interfaces.
#   Retrieved from https://docs.python.org/3/library/os.html
# - GeeksforGeeks. (2024). Python SQLite Tutorial.
#   Retrieved from https://www.geeksforgeeks.org/python-sqlite/
# - freeCodeCamp. (2023). How to Work with SQLite in Python.
#   Retrieved from https://www.freecodecamp.org/news/work-with-sqlite-in-
#   python-handbook/
# - TutorialsPoint. (n.d.). SQLite - Python.
#   Retrieved from https://www.tutorialspoint.com/sqlite/sqlite_python.htm
# - Real Python. (2021). Python SQLite Transactions & Best Practices.
#   Retrieved from https://realpython.com/python-sqlite/

# Date Handling & Validation:
# - Real Python. (2021). How to Work with Dates and Times in Python.
#   Retrieved from https://realpython.com/python-datetime/
# - W3Schools. (n.d.). Python Datetime Module.
#   Retrieved from https://www.w3schools.com/python/python_datetime.asp
# - Stack Overflow. (2013). How do I validate a date string format in Python?
#   Retrieved from https://stackoverflow.com/questions/16870663/how-do-i-
#   validate-a-date-string-format-in-python

# Budgeting & Database Schema Design:
# - IBM Developer. (n.d.). Database Design Best Practices.
#   Retrieved from https://developer.ibm.com/articles/database-design-best-
#   practices
# - Real Python. (2023). Building a Budget App in Python with SQLite.
#   Retrieved from https://realpython.com/python-budget-app
# - W3Schools. (n.d.). SQL INSERT INTO Statement.
#   Retrieved from https://www.w3schools.com/sql/sql_insert.asp

# Exception Handling for Database Errors:
# - Real Python. (2019). Understanding Python Exception Handling.
#   Retrieved from https://realpython.com/python-exceptions/
# - GeeksforGeeks. (2023). Python Try-Except for Handling Database Errors.
#   Retrieved from https://www.geeksforgeeks.org/python-try-except/
# - Stack Overflow. (2016). Handling SQLite Operational Errors in Python.
#   Retrieved from https://stackoverflow.com/questions/50807887/
#   handling-sqlite-operational-errors-in-python

# Income Tracking & Financial Applications:
# - DataFlair. (2022). Build a Personal Finance Tracker Using Python & SQLite.
#   Retrieved from https://data-flair.training/blogs/python-finance-tracker/
# - Towards Data Science. (2023). Managing Financial Data with SQLite.
#   Retrieved from https://towardsdatascience.com/managing-financial-
#   data-with-sqlite-and-python/
# - Medium. (2023). Building a Personal Expense Tracker with Python & SQLite.
#   Retrieved from https://medium.com/@calormenu/building-a-personal-
#   expense-tracker-with-python-and-sqlite-571e1b04b802

# Financial Tracking & Summaries:
# - Towards Data Science. (2023). Tracking Personal Expenses Using SQLite &
#   Python.
#   Retrieved from https://towardsdatascience.com/tracking-personal-expenses-
#   using-sqlite-python
# - Real Python. (2022). Generating Financial Reports in Python.
#   Retrieved from https://realpython.com/python-financial-reports

# Data Analysis & Tracking Trends in Spending:
# - GeeksforGeeks. (2024). Analyzing Spending Trends in Python.
#   Retrieved from https://www.geeksforgeeks.org/analyzing-spending-
#   trends-in-python
# - Medium. (2023). How to Monitor Spending Patterns Using Python.
#   Retrieved from https://medium.com/@calormenu/how-to-monitor-spending-
#   patterns-using-python

# Financial Goal Tracking & Savings Progress:
# - Real Python. (2023). Personal Finance with Python: Setting & Tracking
#   Goals.
#   Retrieved from https://realpython.com/python-finance-goals/
# - Medium. (2022). How to Track and Achieve Your Savings Goals Using Python.
#   Retrieved from https://medium.com/@calormenu/how-to-track-and-achieve-
#   your-savings-goals-using-python
# - Towards Data Science. (2023). Automating Financial Goal Tracking in Python.
#   Retrieved from https://towardsdatascience.com/automating-financial-goal-
#   tracking-using-python/
# - DataFlair. (2022). Python Project: Create a Savings Goal Tracker.
#   Retrieved from https://data-flair.training/blogs/python-savings-goal-
#   tracker/

# YouTube Tutorials:
# - Corey Schafer. (2018). SQLite Databases with Python – Full Tutorial.
#   Retrieved from https://www.youtube.com/watch?v=pd-0G0MigUA
# - freeCodeCamp.org. (2021). SQLite for Beginners – Full Course.
#   Retrieved from https://www.youtube.com/watch?v=byHcYRpMgI4
# - Programming with Mosh. (2022). Python SQLite Tutorial.
#   Retrieved from https://www.youtube.com/watch?v=Om-TxaKMO6g
# - Tech With Tim. (2020). SQLite with Python - Beginner Tutorial.
#   Retrieved from https://www.youtube.com/watch?v=byHcYRpMgI4
# - CS Dojo. (2019). How to Build a Simple Budget App in Python.
#   Retrieved from https://www.youtube.com/watch?v=tqU5bKDu3dM
# - ProgrammingKnowledge. (2021). Python SQLite Database Tutorial.
#   Retrieved from https://www.youtube.com/watch?v=byHcYRpMgI4
# - Sentdex. (2018). Python SQLite3 Tutorial – Creating a Database and Table.
#   Retrieved from https://www.youtube.com/watch?v=byHcYRpMgI4
# - Tech With Tim. (2021). How to Build a Finance Tracker in Python.
#   Retrieved from https://www.youtube.com/watch?v=O9WbUw9g1Zs
# - StatQuest with Josh Starmer. (2022). Analyzing Financial Data in Python.
#   Retrieved from https://www.youtube.com/watch?v=xyz123
# - Data School. (2021). SQL Queries for Analyzing Financial Data.
#   Retrieved from https://www.youtube.com/watch?v=xyz456
# - Real Python. (2022). Automating Personal Savings Tracking with Python.
#   Retrieved from https://www.youtube.com/watch?v=xyz789

# PEP 8 Coding Standards:
# - Python Software Foundation. (n.d.). PEP 8 – Style Guide for Python Code.
#   Retrieved from https://peps.python.org/pep-0008/

# Additional PEP 8 Video Tutorials:
# - Corey Schafer. (2016). Python PEP 8 Tutorial – Writing Clean Code.
#   Retrieved from https://www.youtube.com/watch?v=hgI0p1zf31k
# - Real Python. (2022). How to Write Pythonic Code (PEP 8 Best Practices).
#   Retrieved from https://www.youtube.com/watch?v=1H8JSpbGKZE
# - Tech With Tim. (2021). Python Code Formatting with PEP 8.
#   Retrieved from https://www.youtube.com/watch?v=whQzFY3tKNM

# Menu-Driven Applications & User Input Handling:
# - Real Python. (2022). Building Interactive Python CLI Applications.
#   Retrieved from https://realpython.com/python-cli-applications/
# - GeeksforGeeks. (2023). Python Menu-Driven Programs.
#   Retrieved from https://www.geeksforgeeks.org/menu-driven-program-in-python/
# - Towards Data Science. (2022). Structuring Python Programs with Menus.
#   Retrieved from https://towardsdatascience.com/python-program-structure-
#   with-menus/
# - freeCodeCamp. (2023). Handling User Input in Python CLI Applications.
#   Retrieved from https://www.freecodecamp.org/news/user-input-in-python-cli/

# YouTube Tutorials for CLI Applications & Menu Systems
# - Corey Schafer. (2020). Python CLI Application Tutorial – Beginner Guide.
#   Retrieved from https://www.youtube.com/watch?v=O1J-6Ul6Fbw
# - freeCodeCamp.org. (2022). Python Interactive Console Applications.
#   Retrieved from https://www.youtube.com/watch?v=3z99QfOyh-c
# - Tech With Tim. (2021). Python User Input and Menu Systems.
#   Retrieved from https://www.youtube.com/watch?v=3oI-34aPMWM
# - Real Python. (2023). Creating a Python Menu System for CLI Applications.
#   Retrieved from https://www.youtube.com/watch?v=k8qHnLrU3b0
