import MySQLdb
from flask_mysqldb import MySQL
from flask import Flask, render_template, url_for, request, session
from flask_cors import CORS

# Create flask app
app = Flask(__name__)
CORS(app)
app.secret_key="vende_todo"

# Create connection to DB
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'vende_todo'
mysql = MySQL(app)

# Method to create cursor and execute SELECT queries from DB
def select_from_db(query):
    curs = mysql.connection.cursor()
    try:
        curs.execute(query)
        data = curs.fetchall()
    except MySQLdb.ProgrammingError:
        data = []
    return data

# Method to create cursor and execute INSERT queries from DB
def insert_into_db(query):
    insertCurs = mysql.connection.cursor()
    try:
        insertCurs.execute(query)
        mysql.connection.commit()
        insertCurs.close()
    except MySQLdb.ProgrammingError:
        pass


# Register page
@app.route('/', methods=['POST', 'GET'])
def index():
    try:
        if session['user_id']:
            session['user_id'] = ''
        else:
            session['user_id'] = ''
    except KeyError:
        session['user_id'] = ''
    return "Hello"

# Register page
@app.route('/register', methods=['POST', 'GET'])
def register():
    error = ''
    if request.method == 'POST':
        name = request.form['name']
        lastname = request.form['lastname']
        email = request.form['email']
        passw = request.form['passw']
        telephone = request.form['telephone']
        date = request.form['date']
        print(email, passw, name, lastname, telephone, date)

        # Check if user exists
        users = select_from_db(f""" SELECT user_id FROM user WHERE email = '{email}' """)
        print(users[0][0])

        # If user exists, send error
        if users:
            error = 'Este correo ya esta registrado'
            return render_template('register.html', error=error)
        else:
            # Insert user in database
            insert_into_db(f"""INSERT INTO user(email, password, name, lastname, telephone, type) VALUES('{email}', '{passw}', '{name}', '{lastname}', '{telephone}', 1)""")

            # Get user_id
            user = select_from_db(f""" SELECT user_id FROM user WHERE email = '{email}' """)
            user_id = user[0][0]
            session['user_id'] = user_id
            return render_template('index.html')
    
    return render_template('register.html', error=error)

# Product search page
@app.route('/search', methods=['POST', 'GET'])
def search():
    products = []
    if request.method == 'POST':
        searchParams = request.form.get('params')
        if searchParams:
            # Select products with search params in product title or description 
            products = select_from_db(f""" SELECT * FROM  product WHERE prod_name LIKE '%{searchParams}%' OR description LIKE '%{searchParams}%' """)
            if products:
                products = products[0]
        print(products)

        return render_template('search.html', products=products, amount=len(products))

    return render_template('search.html', products=products, amount=len(products))

@app.route('/product', methods=['POST', 'GET'])
def product_page():
    product = []
    images = []
    if request.method == 'POST':
        # Note: Get prod_id from session redirect here
        prod_id = request.form.get('prod_id')
        # prod_id = session['prod_id']
        images = select_from_db(f"""SELECT prodim.img_id, image.image
                                    FROM image INNER JOIN
                                        (SELECT img_id
                                        FROM prod_image INNER JOIN 
                                            (SELECT * FROM product WHERE {prod_id} = 1) AS p
                                        ON p.prod_id = prod_image.prod_id) AS prodim
                                    ON image.img_id = prodim.img_id 
                                """)
        product = select_from_db(f"""SELECT * FROM product where prod_id = {prod_id} """)
        
        if images:
            images = images[0]
        if product:
            product = product[0]
        print(images)
        print(product)
        return render_template('product.html', product=product, images=images)

    return render_template('product.html', product=product, images=images)

# Run app
if __name__ == "__main__":
    app.run(debug=True)