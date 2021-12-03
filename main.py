import os
import re
import datetime
import secrets
from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
# from flask_pymongo import PyMongo
from pymongo import MongoClient
from flask_login import LoginManager, current_user, login_user, logout_user
from forms import NewProductForm, LoginForm, SignUpForm, ValidateForm, editProductForm, editProfileForm
from models import User, AnonymousUser, permission_required, admin_required, CustomJSONEncoder, login_required, Product
from bson.json_util import ObjectId
from flask_mail import Mail, Message

class Config:
  SECRET_KEY = '7d441f27d441f27567d441f2b6176a'
  MAIL_SERVER = 'smtp.gmail.com'
  MAIL_PORT = 587
  MAIL_USE_TLS = True
  MAIL_USERNAME = 'wumarket889@gmail.com'
  MAIL_PASSWORD = 'wumarket!'
  RESUME_LINK = os.environ.get("RESUME_LINK")
  MAIL_DEFAULT_SENDER = 'wumarket889@gmail.com'
  TESTING = False
  MONGO_URI = "mongodb+srv://wumarket.k8wsz.mongodb.net/myFirstDatabase?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"

mail = Mail()
app = Flask(__name__)
app.config.from_object(Config)
app.json_encoder = CustomJSONEncoder
mail.init_app(app)

# Login stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(id):
  id = ObjectId(id)
  queried_user = db.Users.find_one({"_id":id})
  user = User(queried_user)
  return user

# initialize mongo db
uri = "mongodb+srv://wumarket.k8wsz.mongodb.net/myFirstDatabase?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"
certificate_path = './X509-cert-5700102249016803480.pem'
client = MongoClient(uri,
                     tls=True,
                     tlsCertificateKeyFile=certificate_path)
db = client['WUmarket']


# views
@app.route('/', methods=['GET'])
@login_required
def index():
  print("curren user:", current_user)
  products = db.Products.find(None)
  return render_template('main.html', items=products, db=db)


@app.route('/my_products', methods=['GET'])
@login_required
def my_products():
  products = db.Products.find({"seller_id": ObjectId(current_user.id)})
  return render_template('my_products.html', items=products, db=db)
  
@app.route('/favorites', methods=['GET'])
@login_required
def favorites():
  user = load_user(current_user.id)
  products = db.Products.find({"_id": {"$in": user.favorites}})
  return render_template('main.html', items=products, db=db)

@app.route('/login', methods=['GET', 'POST'])
def login():
  form = LoginForm()
  if request.method == "POST":
    email = request.form['email']
    password = request.form['password']
    queried_user = db['Users'].find_one({"email":email})
    hashed_pw = queried_user['password_hash']
    if check_password_hash(hashed_pw, password):
      user = User(queried_user)
      login_user(user)
      print("Login successfully")
      return redirect(url_for('index'))
    else:
      print("Wrong credentials")
      return redirect(url_for('login'))
  return render_template('login.html', form=form)


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
  form = SignUpForm()
  if request.method == "POST":
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    password = request.form['password']
    email = request.form['email']
    email_regex = re.compile(r"^[\w!#$%&'*+/=?^_`{|}~-]+@([\w\-]+(?:\.[\w\-]+)+)$")
    domain_from_email = None
    match = email_regex.match(email)
    if match is not None:
      domain_from_email = match.group(1)
    if (domain_from_email is not None) and (domain_from_email != 'wustl.edu'):
      return "<h1> Email is not a valid WashU email </h1>", 400
    token = secrets.token_hex(10)
    pw_hash = generate_password_hash(password)
    new_user = { 
           'firstName': firstName,
           'lastName': lastName, 
           'password_hash': pw_hash,
           'email': email,
      # the permission is 0 until confirmed
           'permission': 0,
           'img_link': '',
           'score': 0,
           'vote_counts': 0,
           'token': token,
           'favorites': [],
           'bio': '',
           'title': 'student'
          }
    users = db.Users
    if users.find_one({"email":email}):
      return "<h1> Email already used </h1>", 400
    new_user_id = users.insert_one(new_user).inserted_id
    msg = Message("Verify your WashU email", recipients=[email])
    msg.body = "Your verification code is: " + token + " Visit" +  url_for('validate') + "to validate"
    mail.send(msg)
    print("create new user with id", new_user_id)
    return redirect(url_for('validate')) 
  return render_template('signup.html', form=form)

@app.route('/validate', methods=['GET', 'POST'])
def validate():
  form = ValidateForm()
  if request.method == "POST":
    user_token = request.form['token']
    email = request.form['email']
    if email is not None:
      queried_user = db['Users'].find_one({"email":email})
      user = User(queried_user)
      if user_token == user.token:
        db.Users.update_one({'_id': user.id}, {'$set': {'permission': 1}})
    else:
      return  "<h1> Email invalid </h1>", 400
    return redirect(url_for('index')) 
  return render_template('validate.html', form=form)
        
    

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
  form = NewProductForm()
  if request.method == "POST":
    print("form submitted")
    cur_time = str(datetime.datetime.now())
    # to get datetime object, datetime.datetime.strptime(cur_time, '%Y-%m-%d %H:%M:%S.%f')
    new_product = { 
           'title': request.form['title'],
           'price': request.form['price'],
           'image_link': request.form['image_link'], 
           'description': request.form['description'],
           'tags': [],
           'seller_id': current_user.id,
           'sold': False,
           'post_date': cur_time 
          }

    new_product_id = db.Products.insert_one(new_product).inserted_id
    print("create new product with id", new_product_id)
    return redirect(url_for('index'))

  return render_template('new_post.html', form=form)

@app.route('/add_favorite/<item_id>')
def add_favorite(item_id):
  print("received: ", item_id)
  print(type(item_id))
  item_id = ObjectId(item_id)
  user = load_user(current_user.id)
  if (item_id in user.favorites):
    db.Users.update_one({'_id': current_user.id}, {'$pullAll': {'favorites': [item_id]}})
  else:
    db.Users.update_one({'_id': current_user.id}, {'$push': {'favorites': item_id}})
  return redirect(url_for('index'))

@app.route('/test', methods=['GET', 'POST'])
def test():
  Products = db.Products
  prod = Products.find_one()
  print(prod)
  return "testing"

@app.route('/view_profile/<profile_id>', methods=['GET'])
def view_profile(profile_id):
  profile_id = ObjectId(profile_id)
  profile = db.Users.find_one({"_id": profile_id})
  user = User(profile)
  products = db.Products.find({"seller_id": profile_id})
  current_id = current_user.id
  return render_template('view_profile.html', profile=user, items=products, current_id=current_id, db=db)

@app.route('/delete_product/<item_id>')
def delete_product(item_id):
  print("received: ", item_id)
  item_id = ObjectId(item_id)
  db.Products.delete_one({'_id': item_id})
  return redirect(url_for('my_products'))

@app.route('/edit_product/<item_id>', methods=['GET', 'POST'])
def edit_product(item_id):
  form = editProductForm()
  item_id = ObjectId(item_id)
  product = db.Products.find_one({"_id": item_id})
  
  if request.method == "POST":
    print("form submitted")
    sold = request.form['sold']
    if (sold == 'True'):
      sold = True
    else: 
      sold = False
    updated_data = {
    'title': request.form['title'],
    'price': request.form['price'],
    'image_link': request.form['image_link'], 
    'description': request.form['description'],
    'sold': sold
    }
    db.Products.update_one({'_id': item_id}, {'$set': updated_data})
    return redirect(url_for('my_products'))
  else:
    product = Product(product)
    form.title.data = product.title
    form.price.data = product.price
    form.image_link.data = product.image_link
    form.description.data = product.description
    return render_template('edit_product.html', form=form)
  
@app.route('/edit_profile/<user_id>', methods=['GET', 'POST'])
def edit_profile(user_id):
  form = editProfileForm()
  user_id = ObjectId(user_id)
  profile = db.Users.find_one({"_id": user_id})
  if request.method == "POST":
    print("form submitted")
    updated_data = {
    'firstName': request.form['firstName'],
    'lastName': request.form['lastName'],
    'img_link': request.form['img_link'], 
    'bio': request.form['bio'],
    'title' : request.form['title']
    }
    db.Users.update_one({'_id': user_id}, {'$set': updated_data})
    return redirect(url_for('view_profile', profile_id=user_id))
  else:
    user = User(profile)
    form.firstName.data = user.firstName
    form.lastName.data = user.lastName
    form.img_link.data = user.img_link
    form.bio.data = user.bio
    form.title.data = user.title
    return render_template('edit_profile.html', form=form)
  

@app.route('/private/<path:filename>')
def private(filename):
  file_folder = os.path.join(os.getcwd(), 'private')
  # print("sending", filename, "form", file_folder)
  return send_from_directory(
      file_folder,
      filename
    )



# @app.route('/<anything>')
# def abort_404(anything):
# 	return abort(404)



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)