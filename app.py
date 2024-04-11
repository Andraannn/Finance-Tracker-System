from flask import Flask, render_template, request, redirect, url_for
import psycopg2

app = Flask(__name__)

# Replace these with your PostgreSQL credentials
DB_NAME = 'finance_tracker'
DB_USER = 'postgres'
DB_PASSWORD = '@ptx_4869'
DB_HOST = 'localhost' # or your database host
DB_PORT = '5432'

TRANSACTIONS_PER_PAGE = 5

def connect_to_db():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def create_table():
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    description TEXT,
                    amount NUMERIC,
                    date DATE
                    )''')
    conn.commit()
    conn.close()

create_table()

@app.route('/')
@app.route('/<int:page>')
def index(page=1):
    conn = connect_to_db()
    cur = conn.cursor()
    
    # Fetch transactions and order by date in ascending order
    cur.execute("SELECT * FROM transactions ORDER BY date ASC")
    transactions = cur.fetchall()

    # Reverse the list of transactions to display the oldest transactions last
    transactions.reverse()

    # Calculate current balance
    current_balance = 0
    for transaction in transactions:
        current_balance += transaction[2]  # Assuming amount is at index 2

    # Paginate transactions
    total_transactions = len(transactions)
    total_pages = (total_transactions - 1) // TRANSACTIONS_PER_PAGE + 1
    offset = (page - 1) * TRANSACTIONS_PER_PAGE
    transactions = transactions[offset:offset + TRANSACTIONS_PER_PAGE]

    conn.close()
    return render_template('index.html', transactions=transactions, total_pages=total_pages, page=page, current_balance=current_balance)

@app.route('/edit_transaction', methods=['POST'])
def edit_transaction():
    transaction_id = request.form['transaction_id']
    description = request.form['description']
    amount = float(request.form['amount'])

    # Update the transaction in the database
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("UPDATE transactions SET description = %s, amount = %s WHERE id = %s", (description, amount, transaction_id))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/transaction', methods=['POST'])
def handle_transaction():
    description = request.form['description']
    amount = float(request.form['amount'])
    transaction_type = request.form['transaction_type']  # Get transaction type from form data

    # Determine transaction type based on the submitted form data
    if request.path == '/add':
        transaction_type = 'add'
    elif request.path == '/subtract':
        transaction_type = 'subtract'

    # Adjust amount based on transaction type
    if transaction_type == 'subtract':
        amount = -amount

    # Insert the transaction into the database
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO transactions (description, amount, date) VALUES (%s, %s, CURRENT_DATE)", (description, amount))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/delete_transactions', methods=['POST'])
def delete_transactions():
    # Get list of transaction IDs to delete
    transaction_ids = request.form.getlist('transaction_id')

    # Connect to the database
    conn = connect_to_db()
    cur = conn.cursor()

    # Loop through the list of transaction IDs and delete each transaction
    for transaction_id in transaction_ids:
        cur.execute("DELETE FROM transactions WHERE id = %s", (transaction_id,))
        conn.commit()

    # Close the database connection
    conn.close()

    # Redirect to the index page or wherever appropriate
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
