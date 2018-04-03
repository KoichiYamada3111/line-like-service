from line import db
from sqlalchemy import ForeignKey

expire_days = 14

class TextEntry(db.Model):
	__tablename__ = 'entries'
	id = db.Column(db.Integer, primary_key = True)
	from_user_id = db.Column(db.Integer, db.ForeignKey('members.user_id'))
	to_user_id = db.Column(db.Integer, db.ForeignKey('members.user_id'))
	text = db.Column(db.Text)
	read = db.Column(db.Boolean)
#	sent = db.Column(db.Boolean)
	date = db.Column(db.Text)
	
	def __repr__(self):
		return '<TextEntry id={id} from_user_id={from_user_id} to_user_id={to_user_id} read={read} date={date}>'.format(
		id=self.id, from_user_id=self.from_user_id, to_user_id=self.to_user_id, read=self.read, date=self.date)


class Member(db.Model):
	__tablename__ = 'members'
	user_id = db.Column(db.Integer, primary_key = True)
	password = db.Column(db.Text, nullable=False)
	username = db.Column(db.String(50), nullable=False)
	phone_number = db.Column(db.String(15), nullable=True)
	email = db.Column(db.String(80), nullable=False)
	ic_stored = db.Column(db.Text, nullable=True)
	bg_stored = db.Column(db.Text, nullable=True)
	comment = db.Column(db.Text, nullable=True)
	official = db.Column(db.Boolean, nullable=False)
	
	def __repr__(self):
		return '<Member user_id={user_id} username={username} phone_number={phone_number} email={email} ic_stored={ic_stored} bg_stored={bg_stored}>'.format(
		user_id=self.user_id, username=self.username, phone_number=self.phone_number, email=self.email, ic_stored=self.ic_stored, bg_stored=self.bg_stored)


class Friend(db.Model):
	__tablename__ = 'friends'
	id = db.Column(db.Integer, primary_key = True)
	user_1 = db.Column(db.Integer, db.ForeignKey('members.user_id'))
	user_2 = db.Column(db.Integer, db.ForeignKey('members.user_id'))
	
	def __repr__(self):
		return '<Friend id={id} user_1={user_1} user_2={user_2}>'.format(
		id=self.id, user_1=self.user_1, user_2=self.user_2)

class Post(db.Model):
	__tablename__ = 'posts'
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('members.user_id'))
	date = db.Column(db.Text)
	text = db.Column(db.Text)
	img_name = db.Column(db.Text)
	
	def __repr__(self):
		return '<Post id={id} user_id={user_id} date={date} img_name={img_name}>'.format(
		id=self.id, user_id=self.user_id, date=self.date, img_name=self.img_name)

class LikePost(db.Model):
	__tablename__ = 'likes'
	id = db.Column(db.Integer, primary_key=True)
	post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
	user_id = db.Column(db.Integer, db.ForeignKey('members.user_id'))
	comment = db.Text(db.Text)

def init():
	db.create_all()

def refresh():
	from datetime import timedelta, datetime
	nw = datetime.now()
	i = TextEntry.query.order_by(TextEntry.id.asc()).first().id
	delete_list = []
	expiration = timedelta(days = expire_days)
	while(True):
		tag = TextEntry.query.filter_by(id=i).first()
		if nw - tag.date > expiration:
			delete_list.append(tag)
		else:
			break
		i += 1
	db.session.delete(delete_list)
	db.session.commit()


