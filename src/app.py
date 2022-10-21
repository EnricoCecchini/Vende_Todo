import MySQLdb
from flask_mysqldb import MySQL
from flask import Flask, render_template, url_for, request, session, redirect
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

# Index page
@app.route('/', methods=['POST', 'GET'])
def index():
    try:
        if not session['user_id']:
            session['user_id'] = ''
    except KeyError:
        session['user_id'] = ''
    return render_template('index.html')

# Login Page
@app.route('/login', methods=['POST', 'GET'])
def login():
    error = ''
    print(session['user_id'])
    if request.method == 'POST':
        if 'login' in request.form:
            email = request.form.get('email')
            passw = request.form.get('passw')
            print(email, passw)

            # Check if login data is correct
            users = select_from_db(f""" SELECT user_id FROM user WHERE email = '{email}' AND password = '{passw}' """)
            if users:
                user_id = users[0][0]
                session['user_id'] = user_id

                return redirect(url_for('profile'))
            
            else:
                error = 'El usuario o contrasena es incorrecto'
                return render_template('login.html', error=error)
        
        elif 'signout' in request.form:
            session['user_id'] = ''
            return redirect(url_for('index'))

    return render_template('login.html', error=error)

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
        date = str(request.form['date'])
        print(email, passw, name, lastname, telephone, date)

        # Check if user exists
        users = select_from_db(f""" SELECT user_id FROM user WHERE email = '{email}' """)
        #print(users[0][0])

        # If user exists, send error
        if users:
            error = 'Este correo ya esta registrado'
            return render_template('register.html', error=error)
        else:
            # Insert user in database
            insert_into_db(f""" INSERT INTO user(email, password, name, lastname, telephone, date_of_birth, type) 
                                VALUES('{email}', '{passw}', '{name}', '{lastname}', '{telephone}', '{date}', 1)
                            """)

            # Get user_id
            user = select_from_db(f""" SELECT user_id FROM user WHERE email = '{email}' """)
            user_id = user[0][0]
            session['user_id'] = user_id
            return redirect(url_for('add_address'))
    
    return render_template('register.html', error=error)

# Add address
@app.route('/add_address', methods=['POST', 'GET'])
def add_address():
    error = ''
    if request.method == 'POST':
        user_id = session['user_id']
        street = request.form['street']
        house_num = request.form['house_num']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        zip_code = str(request.form['zip_code'])
        print(street, house_num, city, state, country, zip_code)

        # Check if user exists
        users = select_from_db(f""" SELECT user_id FROM user WHERE user_id = '{user_id}' """)

        # If user exists, send error
        if users:
            # Insert address in database
            insert_into_db(f""" INSERT INTO address(street, house_number, city, state, country, zip_code) 
                                VALUES('{street}', '{house_num}', '{city}', '{state}', '{country}', '{zip_code}')
                            """)

            # Get address_id
            address = select_from_db(f"""   SELECT address_id FROM address 
                                                WHERE street = '{street}' 
                                                AND house_number = '{house_num}'
                                                AND city = '{city}'
                                                AND state = '{state}'
                                                AND country = '{country}'
                                                AND zip_code = '{zip_code}'
                                            ORDER BY address_id DESC
                                    """)
            
            if address:
                address_id = address[0][0]

                # Link user and Address
                insert_into_db(f""" INSERT INTO lives(user_id, address_id) 
                                VALUES('{user_id}', '{address_id}')
                            """)

            return render_template('index.html')
    
    return render_template('add_address.html', error=error)

# User Profile page
@app.route('/profile', methods=['POST', 'GET'])
def profile():
    error = ''
    user_id = session['user_id']

    user = select_from_db(f""" SELECT * FROM user WHERE user_id = '{user_id}' """)
    if user:
        print(user)
    else:
        print('No login')

    return render_template('profile.html', error=error, user=user)

# Product search page
@app.route('/search', methods=['POST', 'GET'])
def search():
    products = []
    tag_list = select_from_db("""SELECT * FROM tag""")
    print(tag_list)
    if request.method == 'POST':
        searchParams = request.form.get('params')
        prod_tagid = request.form.get('tag_id')
        print(prod_tagid)
        if searchParams:
            # Select products with search params in product title or description 
            if prod_tagid == '0':
                products = select_from_db(f"""  SELECT * 
                                                FROM product
                                                    WHERE prod_name LIKE '%{searchParams}%' 
                                                    OR description LIKE '%{searchParams}%' 
                                            """)
            else:
                products = select_from_db(f"""  SELECT prod_tag.prod_id, prod_name, description, price, prod_condition, stock, date
                                                FROM prod_tag INNER JOIN
                                                    (SELECT * 
                                                        FROM product
                                                        WHERE prod_name LIKE '%{searchParams}%' 
                                                            OR description LIKE '%{searchParams}%') AS p
                                                ON prod_tag.prod_id = p.prod_id
                                                WHERE tag_id = {prod_tagid} """)
            if products:
                products = products[0]

        elif prod_tagid:
            products = select_from_db(f"""  SELECT prod_tag.prod_id, prod_name, description, price, prod_condition, stock, date
                                                FROM prod_tag INNER JOIN
                                                    (SELECT * FROM product) AS p
                                                ON prod_tag.prod_id = p.prod_id
                                                WHERE tag_id = {prod_tagid} """)
            if products:
                products = products[0]
        print(products)

        return render_template('search.html', products=products, amount=len(products), tags=tag_list)

    return render_template('search.html', products=products, amount=len(products), tags=tag_list)

# Product page
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