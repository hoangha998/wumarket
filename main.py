import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
# from flask_pymongo import PyMongo
from pymongo import MongoClient
from flask_login import LoginManager, current_user, login_user, logout_user
from forms import NewProductForm, LoginForm, SignUpForm
from models import User, AnonymousUser, permission_required, admin_required, CustomJSONEncoder, login_required
from bson.json_util import ObjectId

class Config:
	SECRET_KEY = '7d441f27d441f27567d441f2b6176a'
	MAIL_SERVER = 'smtp.gmail.com'
	MAIL_PORT = 587
	MAIL_USE_TLS = True
	MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
	MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
	RESUME_LINK = os.environ.get("RESUME_LINK")
	MAIL_DEFAULT_SENDER = 'hoanghm4@gmail.com'
	TESTING = False
	MONGO_URI = "mongodb+srv://wumarket.k8wsz.mongodb.net/myFirstDatabase?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"

app = Flask(__name__)
app.config.from_object(Config)
app.json_encoder = CustomJSONEncoder

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
		pw_hash = generate_password_hash(password)
		new_user = { 
					 'firstName': firstName,
					 'lastName': lastName, 
					 'password_hash': pw_hash,
					 'email': email,
					 'permission': 1,
					 'img_link': '',
					 'score': 0,
					 'vote_counts': 0 
					}
		users = db.Users
		if users.find_one({"email":email}):
			return "<h1> Email already used </h1>", 400
		new_user_id = users.insert_one(new_user).inserted_id
		print("create new user with id", new_user_id)
		return redirect(url_for('index')) 
	return render_template('signup.html', form=form)


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
	db.Users.update_one({'_id': current_user.id}, {'$push': {'favorites': item_id}})
	return redirect(url_for('index'))
@app.route('/test', methods=['GET', 'POST'])
def test():
	Products = db.Products
	prod = Products.find_one()
	print(prod)
	return "testing"

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
    app.run(host='0.0.0.0', port=5000)