from . import db
from flask_login import UserMixin,AnonymousUserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from . import login_manager
from datetime import datetime
from markdown import markdown
import bleach

# 权限
class Permission:
	FOLLOW = 0x01
	COMMENT = 0x02
	WRITE_ARTICLES = 0x04
	MODERATE_COMMENTS = 0x08
	ADMINISTER = 0x80
#登入要求的
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))
#角色
class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer,primary_key=True)
	name = db.Column(db.String(64),unique=True)
	default = db.Column(db.Boolean,default=False,index=True)
	users = db.relationship('User',backref='role',lazy='dynamic')
	permissions = db.Column(db.Integer)

	#创建角色
	@staticmethod
	def insert_roles():
		roles={
		'User':(Permission.FOLLOW|
			Permission.COMMENT|
			Permission.WRITE_ARTICLES,True),
		'Moderator':(Permission.FOLLOW|
			Permission.COMMENT|
			Permission.WRITE_ARTICLES|
			Permission.MODERATE_COMMENTS,False),
		'Administrator':(0xff,False)
		}
		for r in roles:
			role = Role.query.filter_by(name=r).first()
			if role == None:
				role = Role(name=r)
				role.permissions = roles[r][0]
				role.default = roles[r][1]
				db.session.add(role)
		db.session.commit()

	def __repr__(self):
		return '<Role %r>' % self.name

# # 用户关注关联表
# class Follow(db.Model):
# 	__tablename__ = 'follows'
# 	follower_id = db.Column(db.Integer,db.ForeignKey('users.id'),
# 							primary_key=True)
# 	followed_id = db.Column(db.Integer,db.ForeignKey('users.id'),
# 							primary_key=True)
# 	timestamp = db.Column(db.DateTime,default=datetime.utcnow)


#用户
class User(UserMixin,db.Model):
	__tablename__ = 'users'
	#基本信息
	email = db.Column(db.String(64),unique=True,index=True)
	id = db.Column(db.Integer,primary_key=True)
	username = db.Column(db.String(64),unique=True,index=True)
	role_id = db.Column(db.Integer,db.ForeignKey('roles.id'))
	password_hash = db.Column(db.String(128))

	#用户信息
	name = db.Column(db.String(64))
	about_me = db.Column(db.Text())
	memeber_since = db.Column(db.DateTime(),default=datetime.utcnow)
	last_seen = db.Column(db.DateTime(),default=datetime.utcnow)

	#文章关系
	posts = db.relationship('Post',backref='author',lazy='dynamic')

	#评论关系
	comments = db.relationship('Comment',backref='author',lazy='dynamic')

	# #用户关注多对多关系
	# followed = db.relationship('Follow',
	# 							foreign_keys=[Follow.follower_id],
	# 							backref=db.backref('follower',lazy='joined'),
	# 							lazy='dynamic',
	# 							cascade='all, delete-orphan')
	# follower = db.relationship('Follow',
	# 							foreign_keys=[Follow.followed_id],
	# 							backref=db.backref('followed',lazy='joined'),
	# 							lazy='dynamic',
	# 							cascade='all,delete-orphan')

	# ## 关注的辅助方法
	# def follow(self,user):
	# 	if not self.is_following(user):
	# 		f = Follow(follower=self,followed=user)
	# 		db.session.add(f)

	# def unfollow(self,user):
	# 	f = self.followed.filter_by(followed_id=user.id).first()
	# 	if f:
	# 		db.session.delete(f)

	# def is_following(self,user):
	# 	return self.followed.filter_by(followed_id=user.id).first() is not None

	# def is_followed_by(self,user):
	# 	return self.follower.filter_by(follower_id=user.id).first() is not None





	#刷新最后访问的时间
	def ping(self):
		self.last_seen = datetime.utcnow()
		db.session.add(self)

	#权限检测
	def can(self,permissions):
		return self.role is not None and\
		(self.role.permissions&permissions) == permissions
	#检测是否管理员
	def is_administrator(self):
		return self.can(Permission.ADMINISTER)
	#设定密码
	@property
	def password(self):
		raise AttributeError("password is not a readable attribute!")

	@password.setter
	def password(self,password):
		self.password_hash = generate_password_hash(password)
	#验证密码
	def verify_password(self,password):
		return check_password_hash(self.password_hash,password)

	def __repr__(self):
		return '<User %r>'%self.username

	#生成虚拟数据
	@staticmethod
	def generate_fake(count=100):
		from sqlalchemy.exc import IntegrityError
		from random import seed
		import forgery_py

		seed()
		for i in range(count):
			u = User(username=forgery_py.internet.user_name(True),
				role_id=1,
				password=forgery_py.lorem_ipsum.word(),
				name=forgery_py.name.full_name(),
				about_me=forgery_py.lorem_ipsum.sentence(),
				memeber_since=forgery_py.date.date(True))
			db.session.add(u)
			try:
				db.session.commit()
			except IntegrityError:
				db.session.rollback()

#游客
class AnonymousUser(AnonymousUserMixin):
	def can(self,permissions):
		return False
	def is_administrator(self):
		return False
login_manager.anonymous_user = AnonymousUser

# 文章模型
class Post(db.Model):
	__tablename__ = 'posts'
	id = db.Column(db.Integer,primary_key=True)
	title = db.Column(db.String(64))
	subtitle = db.Column(db.String(64))
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	body_browse = db.Column(db.Text)
	body_browse_html= db.Column(db.Text)
	timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
	author_id = db.Column(db.Integer,db.ForeignKey('users.id'))

	#评论关系
	comments = db.relationship('Comment',backref='post',lazy='dynamic')

	@staticmethod
	def on_changed_body(target,value,oldvalue,initiator):
		target.body_browse=value[:200]
		allowed_tags=['a','abbr','acronym','b','blockquote','code',
		'em','i','li','ol','pre','strong','ul','h1','h2','h3','p'] 
		target.body_html=bleach.linkify(bleach.clean(markdown(value,output_format='html'),
			tags=allowed_tags,strip=True))

	@staticmethod

	def on_change_body_browse(target,value,oldvalue,initiator):
		allowed_tags=['a','abbr','acronym','b','blockquote','code',
		'em','i','li','ol','pre','strong','ul','h1','h2','h3','p'] 
		target.body_browse_html=bleach.linkify(bleach.clean(markdown(value,output_format='html'),
			tags=allowed_tags,strip=True))


	@staticmethod
	def generate_fake(count=100):
		from random import seed,randint
		import forgery_py

		seed()
		user_count = User.query.count()
		for i in range(count):
			u = User.query.offset(randint(0,user_count-1)).first()
			p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1,3)),
				timestamp=forgery_py.date.date(True),
				title=forgery_py.lorem_ipsum.sentence(),
				author=u)
			db.session.add(p)
			db.session.commit()

class Comment(db.Model):
	__tablename__='comments'
	id = db.Column(db.Integer,primary_key=True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
	disabled = db.Column(db.Boolean)
	author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
	post_id = db.Column(db.Integer,db.ForeignKey('posts.id'))

	@staticmethod
	def on_changed_body(target,value,oldvalue,initiator):
		allowed_tags=['a','abbr','acronym','b','code','em','i',
		'strong']
		target.body_html = bleach.linkify(bleach.clean(markdown(value,output_format='html'),
			tags=allowed_tags,strip=True))


#监听
db.event.listen(Comment.body,'set',Comment.on_changed_body)
db.event.listen(Post.body,'set',Post.on_changed_body)
db.event.listen(Post.body_browse,'set',Post.on_change_body_browse)
