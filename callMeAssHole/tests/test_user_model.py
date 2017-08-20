import unittest
from app.models import User,Permission,Role,AnonymousUser
from flask import current_app
from app import create_app,db

class UserModelTestCase(unittest.TestCase):
	def setUp(self):
		self.app = create_app('testing')
		self.app_context = self.app.app_context()
		self.app_context.push()
		db.create_all()

	def tearDown(self):
		db.session.remove()
		db.drop_all()
		self.app_context.pop()

	def test_password_setter(self):
		u = User(password='cat')
		self.assertTrue(u.password_hash is not None)

	def test_no_password_getter(self):
		u = User(password='cat')
		with self.assertRaises(AttributeError):
			u.password
	def test_password_verification(self):
		u = User(password = 'cat')
		self.assertTrue(u.verify_password('cat'))
		self.assertFalse(u.verify_password('dog'))

	def test_password_salts_are_random(self):
		u = User(password= 'cat')
		u2 = User(password= 'cat')
		self.assertTrue(u.password_hash != u2.password_hash)

	def test_roles_and_user_permissions(self):
		Role.insert_roles()
		u = User(username='john1',password='cat',
			role = Role.query.filter_by(default=True).first())
		self.assertTrue(u.can(Permission.FOLLOW))
		self.assertTrue(u.can(Permission.COMMENT))
		self.assertTrue(u.can(Permission.WRITE_ARTICLES))
		self.assertFalse(u.can(Permission.MODERATE_COMMENTS))
		self.assertFalse(u.can(Permission.ADMINISTER))

	def test_moderator_permission(self):
		Role.insert_roles()
		u = User(username='john2',password='cat',
			role = Role.query.filter_by(name='Moderator').first())
		self.assertTrue(u.can(Permission.FOLLOW))
		self.assertTrue(u.can(Permission.COMMENT))
		self.assertTrue(u.can(Permission.WRITE_ARTICLES))
		self.assertTrue(u.can(Permission.MODERATE_COMMENTS))
		self.assertFalse(u.can(Permission.ADMINISTER))

	def test_administrator_permission(self):
		Role.insert_roles()
		u = User(username='john3',password='cat',
			role = Role.query.filter_by(name='Administrator').first())
		self.assertTrue(u.can(Permission.FOLLOW))
		self.assertTrue(u.can(Permission.COMMENT))
		self.assertTrue(u.can(Permission.WRITE_ARTICLES))
		self.assertTrue(u.can(Permission.MODERATE_COMMENTS))
		self.assertTrue(u.can(Permission.ADMINISTER))


	def test_anonymous_permission(self):
		u = AnonymousUser()
		self.assertFalse(u.can(Permission.FOLLOW))
		self.assertFalse(u.can(Permission.COMMENT))
		self.assertFalse(u.can(Permission.WRITE_ARTICLES))
		self.assertFalse(u.can(Permission.MODERATE_COMMENTS))
		self.assertFalse(u.can(Permission.ADMINISTER))