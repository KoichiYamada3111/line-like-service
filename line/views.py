from flask import request, redirect, url_for, render_template, session, flash
from line import app, db, bcrypt
from line.models import TextEntry, Member, Friend, Post, LikePost
from sqlalchemy import or_, and_
from werkzeug import secure_filename
#import PIL.Image

from datetime import datetime
import os

# 各route()関数の前に実行される処理
@app.before_request
def before_request():
	session['path'] = os.path.dirname(os.path.abspath(__file__))
	if session.get('user_id') is not None:
		return
	if request.path == '/login':
		return
	if request.path == '/register':
		return
	if request.path == '/':
		return
#	if request.path == '/test':
#		return
	return redirect('/login')
	
# ログインページに飛ぶ
@app.route('/', methods=['GET'])
def index():
	if session.get('user_id') is not None:
		return redirect(url_for('show_entries', from_user_id = session.user_id))
	else:
		return render_template('top.html')

# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
	warning = None
	if request.method == 'POST':
		if is_account_valid():
			user_tag = Member.query.filter_by(email = request.form['email']).first()
			session['user_id'] = user_tag.user_id
			flash('Successfully logged in!')
			return redirect(url_for('show_entries', from_user_id=session['user_id']))
		warning = 'Incorrect information'
	return render_template('login.html', warning=warning)
	
# 正規のアカウントかチェックする
def is_account_valid():
	mem = Member.query.filter_by(email = request.form['email']).first()
	if mem:
		if bcrypt.check_password_hash(mem.password, request.form['password']):
			return True
	return False

# ログアウト
@app.route('/logout', methods=['GET'])
def logout():
	session.pop('user_id', None)
	flash('Successfully logged out!')
	return redirect(url_for('login'))


# アカウント登録
@app.route('/register', methods=['GET','POST'])
def register():
	warning = None
	if request.method == 'POST':
		if is_user_info_valid():
			str_user_id = str(1001 + Member.query.count())
			path = ['static','img',str_user_id]
			img_file_path = os.path.join(session['path'], *path)
			if os.path.exists(img_file_path):
				warning='Delete the files in /static/img'
				return redirect(url_for('logout'))
			os.makedirs(img_file_path)
			add_mem = Member(
				user_id = 1001 + Member.query.count(),
				password = bcrypt.generate_password_hash(request.form['password'], 10),
				username = request.form['username'],
				phone_number = request.form['phone_number'],
				email = request.form['email'],
				ic_stored = None,
				bg_stored = None,
				official = 0,
				comment = 'No Comment',
			)
			db.session.add(add_mem)
			db.session.commit()
			flash('Successfully registered!')
			return redirect('/login')
		warning = 'Invalid Information'
	return render_template('register.html', warning=warning)

# ユーザー情報が有効かどうかを判断
def is_user_info_valid():
	if(request.form.get('username') == '' or request.form.get('password') == ''
	or request.form.get('email') == '' or request.form.get('phone_number') == ''):
		return False
	if(Member.query.filter_by(email=request.form['email']).first() or Member.query.filter_by(phone_number=request.form['phone_number']).first()):
		return False
	return True


# ユーザと交流のあるアカウント一覧を返す
@app.route('/user/<from_user_id>/chat', methods=['GET', 'POST'])
def show_entries(from_user_id):
	if from_user_id != str(session['user_id']):
		return redirect(url_for('login'))
	received = TextEntry.query.filter(
		or_(
			TextEntry.to_user_id == from_user_id,
			TextEntry.from_user_id == from_user_id
		)
	).all()
	received.sort(key=lambda tag: -tag.id)
	received_list = []
	flag_list=[]
	for tag in received:
		id_=None
		if tag.from_user_id == int(from_user_id):
			id_ = tag.to_user_id
		else:
			id_ = tag.from_user_id
		if id_ not in received_list:
			received_list.append(id_)
	id_to_whole_tag = lambda id: Member.query.filter_by(user_id=id).first()
	received_list = list(map(id_to_whole_tag, received_list))
	return render_template('user_list.html', from_mem=received_list)


# フレンド登録
@app.route('/user/<from_user_id>/friend',methods=['GET','POST'])
def friend(from_user_id):
	if from_user_id != str(session['user_id']):
		return redirect(url_for('login'))
	warning = None
	if request.method == 'POST':
		E = request.form['email']
		T = request.form['tel']
		if E:
			user = Member.query.filter_by(email=E).first().user_id
		elif T:
			user = Member.query.filter_by(phone_number=T).first().user_id
		else:
			warning = 'Try submitting again'
			return render_template('friend.html', from_user_id=from_user_id, warning=warning)
		if user == from_user_id:
			warning = 'Try submitting again'
			return render_template('friend.html', from_user_id=from_user_id, warning=warning)
		if is_register_valid(from_user_id, user):
			frnd = Friend(
				user_1 = from_user_id,
				user_2 = user
			)
			db.session.add(frnd)
			db.session.commit()
			flash('Successfully registered!')
			return redirect(url_for('show_entries', from_user_id=from_user_id))
		else:
			warning = 'Already friend'
	return render_template('friend_register.html', from_user_id=from_user_id, warning = warning)

# 新しくフレンド登録するユーザがすでにフレンドであればFalseを返す
def is_register_valid(from_user_id, user):
	if Friend.query.filter_by(user_1 = from_user_id, user_2 = user).first():
		return False
	if Friend.query.filter_by(user_1 = user, user_2 = from_user_id).first():
		return False
	return True


# フレンドリストを返す
@app.route('/user/<from_user_id>/friend_list',methods=['GET'])
def friend_list(from_user_id):
	if from_user_id != str(session['user_id']):
		return redirect(url_for('login'))
	friends = [tag.user_2 for tag in Friend.query.filter_by(user_1 = from_user_id).all()]
	friends = friends + [tag.user_1 for tag in Friend.query.filter_by(user_2 = from_user_id).all()]
	id_to_tag = lambda id: Member.query.filter_by(user_id=id).all()
	friend_list = [element[0] for element in list(map(id_to_tag, friends))]
	return render_template('friend_list.html', friend_list=friend_list)


# 退会する
#@app.route('/user/<user_id>/unsubscribe', methods=['GET','POST'])
#def unsubscribe(from_user_id):
#	entry = Member.query.filter_by(user_id=user_id)
#	db.session.delete(entry)
#	entry=Member(user_id=user_id,password='',username=None,phone_number=None,email=None,ic_stored=None,bg_stored=None,official=0,comment=None)
#	db.session.add(entry)
#	entry = Friend.query.filter(or_(and_(


# 特定のアカウントとのチャットログを返す
@app.route('/user/<from_user_id>/<to_user_id>/chat', methods=['GET', 'POST'])
def show_messages(from_user_id, to_user_id):
	if from_user_id != str(session['user_id']):
		return redirect(url_for('login'))
	entries = TextEntry.query.filter(
		or_(
			and_(
				TextEntry.from_user_id == from_user_id, 
				TextEntry.to_user_id == to_user_id
			), and_(
				TextEntry.from_user_id == to_user_id, 
				TextEntry.to_user_id == from_user_id
			)
		)
	).all()
	entries.sort(key = lambda tag: -tag.id)
	user_data = Member.query.filter_by(user_id=to_user_id).first()
	if Friend.query.filter(or_(
		and_(
			Friend.user_1==from_user_id, 
			Friend.user_2==to_user_id
		), and_(
			Friend.user_1==to_user_id, 
			Friend.user_2==from_user_id
		))
	).first():
		friend_flag=True
	else:
		friend_flag=False
	return render_template('show_messages.html', entries=entries, user=user_data, friend_flag=friend_flag)


# メッセージを送る
@app.route('/user/<from_user_id>/<to_user_id>/add', methods=['POST'])
def add_entry(from_user_id, to_user_id):
	if from_user_id != str(session['user_id']):
		return redirect(url_for('login'))
	entry = TextEntry(
		from_user_id=session['user_id'],
		to_user_id=to_user_id,
		text=request.form['text'],
		read = 0,
		date = datetime.now().strftime('%y/%m/%d %H:%M'),
		)
	db.session.add(entry)
	db.session.commit()
	flash('Successfully sent!')
	return redirect(url_for('show_messages', from_user_id=from_user_id, to_user_id=to_user_id))


# ユーザホーム画面（公式アカウントはより詳細な情報の掲載、機能の充実を予定）
@app.route('/user/<from_user_id>/<user_id>/home', methods=['GET','POST'])
def home(from_user_id, user_id):
	if from_user_id != str(session['user_id']):
		return redirect(url_for('login'))
	user = Member.query.filter_by(user_id=user_id).first()
	posts=Post.query.filter_by(user_id = user_id).all()
	posts.sort(key = lambda tag: -tag.id)
	if user_id == from_user_id:
		edit_flag = 1
	else:
		edit_flag = None
	like_dic={}
	for post in posts:
		if LikePost.query.filter_by(user_id=from_user_id, post_id = post.id).first():
			like_dic[str(post.id)] = True
		else:
			like_dic[str(post.id)] = False
	like_by_post = {}
	for post in posts:
		like_by_post[str(post.id)] = LikePost.query.filter_by(post_id = post.id).count()
#	bg_height = '312px'
#	bg_path = '{root}/line/static/img/{user_id}/bg.{extention}'.format(root=session['path'], user_id=user_id, extention=user.bg_stored)
#	if os.path.exists(bg_path):
#		bg = PIL.Image.open(bg_path)
#		bg_height=str(bg.size[1])+'px'
	return render_template('home.html', user=user, posts=posts, edit_flag=edit_flag, like_dic=like_dic, like_by_post=like_by_post)


# ユーザのアイコンと背景の画像や、基本情報を変更（それによってコンテンツや広告を変える予定）
#@app.route('/user/<user_id>/setting', methods=['GET', 'POST'])
#def setting(user_id):
#	if user_id != str(session['user_id']):
#		return redirect(url_for('login'))
#	if request.method == 'POST':
#		if 'ic' in request.files:
#			ic_file = request.files['ic']
#			if ic_file.filename == '':
#				warning = 'No image title'
#				return render_template('home.html', from_user_id = user_id, user_id=user_id, warning=warning)
#			if allowed_file(ic_file.filename):
#				filename = secure_filename(img_file.filename)
#				path_list = ['static', 'img', str(user_id), ic.]
#				ic_path = os.path.join(session['path'], *path_list)
#				if os.path.exists(ic_path):
#					
#				img_file.save(img_path)
#		if 'img' in request.files:
#			img_file = request.files['img']
#			if img_file.filename == '':
#				warning = 'No image title'
#				return render_template('post.html', usr_id=user_id, warning=warning)
#			if allowed_file(img_file.filename):
#				filename = secure_filename(img_file.filename)
#				path_list = ['static', 'img', str(user_id), filename]
#				img_path = os.path.join(session['path'], *path_list)
#				if os.path.exists(img_path):
#					warning='You already have a image file with the same title'
#					return render_template('post.html', user_id=user_id, warning=warning)
#				img_file.save(img_path)
#
#	user = Member.query.filter_by(user_id=user_id)
#	return render_template('setting.html', user=user)

#@app.route('/user/<user_id>/setting/changing', methods=['POST'])
#def change_setting(user_id):
#	


# プロフィールを投稿、追加
@app.route('/user/<user_id>/add_post', methods=['GET','POST'])
def add_post(user_id):
	if user_id != str(session['user_id']):
		return redirect(url_for('login'))
	if request.method == 'POST':
		if 'img' in request.files:
			img_file = request.files['img']
			if img_file.filename == '':
				warning = 'No image title'
				return render_template('post.html', user_id=user_id, warning=warning)
			if allowed_file(img_file.filename):
				filename = secure_filename(img_file.filename)
				path_list = ['static', 'img', str(user_id), filename]
				img_path = os.path.join(session['path'], *path_list)
				if os.path.exists(img_path):
					warning='You already have a image file with the same title'
					return render_template('post.html', user_id=user_id, warning=warning)
				img_file.save(img_path)
			else:
				warning = 'Unaccepted file extention'
				return render_template('post.html', user_id=user_id, warning=warning)
		else:
			filename = None
		post = Post(
			user_id = user_id,
			date = datetime.now().strftime('%y/%m/%d %H:%M'),
			text = request.form['text'],
			img_name = filename,
		)
		db.session.add(post)
		db.session.commit()
		return redirect(url_for('home', from_user_id=user_id, user_id=user_id))
	return render_template('post.html')
	
# ファイルの名前が有効かどうか
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.')[1].lower() in set(['png','jpg','gif'])


# 一言コメントを変更
@app.route('/user/<from_user_id>/<user_id>/new_comments', methods=['POST'])
def new_comments(from_user_id, user_id):
	if from_user_id != str(session['user_id']):
		return redirect(url_for('login'))
	entry = Member.query.filter_by(user_id=user_id).first()
	entry.comment = request.form['new_comments']
	db.session.commit()
	return redirect(url_for('home', from_user_id=from_user_id, user_id=user_id))
	
	
# 投稿に「いいね」する
@app.route('/user/<user_id>/like_post', methods=['POST'])
def like_post(user_id):
	if user_id != str(session['user_id']):
		return redirect(url_for('login'))
	if request.method == 'POST':
		post = request.form['post']
		comment = request.form['comment']
		if LikePost.query.filter_by(post_id = post.id, user_id = user_id).first():
			warning='You already like the post'
			return redirect(url_for('home', from_user_id = user_id, user_id=post.user_id))
		like = LikePost(
			post_id = post.id,
			user_id = user_id,
			comments = request.form['comment']
		)
		db.session.add(like)
		db.session.commit()
	return redirect(url_for('home', from_user_id=user_id, user_id = post.user_id))
	
	
# 投稿の「いいね」を消す
@app.route('/user/<user_id>/dislike', methods=['POST'])
def dislike_post(user_id):
	if user_id != str(session['user_id']):
		return redirect(url_for('login'))
	if request.method == 'POST':
		post = request.form['post']
		like = LikePost(user_id=user_id, post_id=post.id).first()
		db.session.delete(like)
		db.session.commit()
	return redirect(url_for('home', from_user_id=user_id, user_id = post.user_id))

# テスト
#@app.route('/test', methods=['GET'])
#def test():
#	return render_template('test.html')