import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
# from flask_pymongo import PyMongo
from pymongo import MongoClient
from flask_login import LoginManager, current_user, login_user, logout_user
from forms import NewProductForm, LoginForm, SignUpForm
from models import User, AnonymousUser, permission_required, admin_required, CustomJSONEncoder, login_required
from bson.json_util import ObjectId
from flask_socketio import SocketIO
from flask_socketio import emit, join_room, leave_room
import time

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

# socketio
socketio = SocketIO()
socketio.init_app(app, cors_allowed_origins='*')

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

@app.route('/chats')
def chats():
	cur_id = current_user.id
	chat_history = list(db.Chats.find({'user1_id': cur_id})) + list(db.Chats.find({'user2_id': cur_id}))
	chat_history.sort(key=lambda x: x['timestamp'])

	chat_heads = []
	for chat in chat_history:
		other_user_id = chat['user1_id']
		if cur_id == other_user_id:
			other_user_id = chat['user2_id']
		other_user = db.Users.find_one({'_id': other_user_id})
		other_user_name = '{} {}'.format(other_user['firstName'], other_user['lastName'])
		other_user_img_link = other_user['img_link']
		chat_heads.append({'name': other_user_name,
							'img_link': other_user_img_link,
							'id': str(other_user_id)})

	return render_template('chats.html', chat_heads=chat_heads)


@app.route('/change_chathead', methods=['POST']) 
def change_chathead():
	print("change chathead called")
	session['other_id'] = request.form['other_user_id']

	other_user_id = ObjectId(request.form['other_user_id'])
	cur_id = current_user.id
	if str(cur_id) >= str(other_user_id):
		chat_history = db.Chats.find_one({'user1_id': cur_id,
											'user2_id': other_user_id})
	else:
		chat_history = db.Chats.find_one({'user1_id': other_user_id,
											'user2_id': cur_id})
	messages = chat_history['messages']
	cur_id = str(current_user.id)
	other_id = session['other_id']
	room_id = str(cur_id) + str(other_user_id)
	session['room_id'] = room_id

	# join_room(room_id)
	return jsonify({'messages': messages,
					'cur_user_id': str(cur_id)})

@app.route('/add_message', methods=['POST'])
def add_message():
	# a = request.args.get('a', 0, type=int)
	# print(a)
	print('add_message called')
	if request.method == "POST":
		print("post received")
		cur_id = current_user.id
		other_id = ObjectId(session['other_id'])
		newMes = request.form['message']
		newMesObj = {'message': newMes, 
					'sender_id': cur_id}

		user1_id = other_id
		user2_id = cur_id
		if str(cur_id) >= session['other_id']:
			user1_id = cur_id
			user2_id = other_id
		
		if db.Chats.find_one({'user1_id': user1_id, 'user2_id': user2_id}) is not None:
			db.Chats.update_one({'user1_id': user1_id,
									'user2_id': user2_id},
										{'$push': {'messages': newMesObj},
										 '$set': {'timestamp': time.time()}
								})
		else:
			db.Chats.insert_one({	'user1_id': user1_id,
									'user2_id': user2_id,
									'messages': [newMesObj],
									'timestamp': time.time()
								})

	return jsonify(status='Done')

@app.route('/private/<path:filename>')
def private(filename):
	file_folder = os.path.join(os.getcwd(), 'private')
	# print("sending", filename, "form", file_folder)
	return send_from_directory(
			file_folder,
			filename
		)

clients = dict()
@socketio.on('joined', namespace='/chats')
def joined(message):
	print("joined called")
	cur_id = str(current_user.id)
	other_id = session['other_id']
	clients[cur_id] = request.sid
	if cur_id >= other_id:
		room_id =(cur_id + other_id)
	else:
		room_id = other_id + cur_id
	session['room_id'] = room_id
	print("cur_room: ", room_id)
	join_room(room_id)

@socketio.on('broadcastMessage', namespace='/chats')
def incomingMessage(message):
	other_sid = clients.get(session['other_id'])
	if other_sid is not None:
		room_id = session.get('room_id')
		print("broadcasting message to {} room. Content: {}".format(room_id, message['msg']))
		emit('incomingMessage', {'msg': message['msg'], 'sender_id': str(current_user.id)}, room=room_id)
	else:
		print("Nothing to broadcast, the other user is not online.")


# @app.route('/<anything>')
# def abort_404(anything):
# 	return abort(404)



if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)