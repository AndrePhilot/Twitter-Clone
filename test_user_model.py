"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        """Roll back the transaction to keep the database clean. """
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_dunder_repr(self):
        """Does the repr method work as expected?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        expected_repr = f"<User #{u.id}: {u.username}, {u.email}>"
        actual_repr = repr(u)

        self.assertIn(expected_repr, actual_repr)

    def test_is_following(self):
        """Does is_following successfully detect when
        user1 is following user2 and when user2 is not
        following user1?"""

        user1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        user2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add_all([user1, user2])
        db.session.commit()

        follow = Follows(
            user_being_followed_id=user2.id,
            user_following_id=user1.id)

        db.session.add(follow)
        db.session.commit()

        self.assertEqual(True, user1.is_following(user2))
        self.assertEqual(False, user2.is_following(user1))

    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when
        user1 is followed by user2 and when user2 is not
        followed by user1?"""

        user1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        user2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add_all([user1, user2])
        db.session.commit()

        follow = Follows(
            user_being_followed_id=user1.id,
            user_following_id=user2.id)

        db.session.add(follow)
        db.session.commit()

        self.assertEqual(True, user1.is_followed_by(user2))
        self.assertEqual(False, user2.is_followed_by(user1))

    def test_User_create_non_null_email(self):
        """Does User.create fail to create a new user
        if any of the validations (e.g. uniqueness,
        non-nullable fields) fail?"""

        user = User(
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        with self.assertRaises(IntegrityError):
            try:
                db.session.add(user)
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                raise e

        self.assertIsNone(User.query.filter_by(username=user.username).first())

    def test_User_create_non_null_username(self):
        """Does User.create fail to create a new user
        if any of the validations (e.g. uniqueness,
        non-nullable fields) fail?"""

        user = User(
            email="test1@test.com",
            password="HASHED_PASSWORD"
        )

        with self.assertRaises(IntegrityError):
            try:
                db.session.add(user)
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                raise e

        self.assertIsNone(User.query.filter_by(email=user.email).first())

    def test_User_create_uniqueness_username(self):
        """Does User.create fail to create a new user
        if any of the validations (e.g. uniqueness,
        non-nullable fields) fail?"""

        user1 = User(
            email="test1@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(user1)
        db.session.commit()

        user2 = User(
            email="test2@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        with self.assertRaises(IntegrityError):
            try:
                db.session.add(user2)
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                raise e

        self.assertEqual(1, User.query.filter_by(username=user1.username).count())

    def test_User_create_uniqueness_email(self):
        """Does User.create fail to create a new user
        if any of the validations (e.g. uniqueness,
        non-nullable fields) fail?"""

        user1 = User(
            email="test@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        db.session.add(user1)
        db.session.commit()

        user2 = User(
            email="test@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        with self.assertRaises(IntegrityError):
            try:
                db.session.add(user2)
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                raise e

        self.assertEqual(1, User.query.filter_by(email=user1.email).count())

    def test_User_authentication_valid(self):
        """Does User.authenticate successfully return a
        user when given a valid username and password?"""

        u = User.signup(
            username="testuser",
            email="test@test.com",
            password="HASHED_PASSWORD",
            image_url="/static/default-profile.jpg"
        )

        db.session.commit()

        self.assertIsNotNone(User.authenticate(u.username, u.password))

    def test_User_authentication_invalid_username(self):
        """Does User.authenticate fail to return a
        user when the username is invalid?"""

        u = User.signup(
            username="testuser",
            email="test@test.com",
            password="HASHED_PASSWORD",
            image_url="/static/default-profile.jpg"
        )

        db.session.commit()

        self.assertFalse(User.authenticate("testuser1", u.password))

    def test_User_authentication_invalid_pwd(self):
        """Does User.authenticate fail to return a
        user when the password is invalid?"""

        u = User.signup(
            username="testuser",
            email="test@test.com",
            password="HASHED_PASSWORD",
            image_url="/static/default-profile.jpg"
        )

        db.session.commit()

        self.assertFalse(User.authenticate(u.username, "HASHED_PASSWORD1"))