from werkzeug.security import generate_password_hash,check_password_hash
from . import db
from flask_login import UserMixin,AnonymousUserMixin

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
	number = db.Column(db.Integer)

	about_me = db.Column(db.Text())
	memeber_since = db.Column(db.DateTime(),default=datetime.utcnow)
	last_seen = db.Column(db.DateTime(),default=datetime.utcnow)

	#文章关系
	posts = db.relationship('Post',backref='author',lazy='dynamic')

	#评论关系
	comments = db.relationship('Comment',backref='author',lazy='dynamic')


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
	tags = db.Column(db.Text)
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

class Comment(db.Model):
	__tablename__='comments'
	id = db.Column(db.Integer,primary_key=True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
	disabled = db.Column(db.Boolean)
	author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
	post_id = db.Column(db.Integer,db.ForeignKey('posts.id'))
	unread = db.Column(db.Boolean,default=True)

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
