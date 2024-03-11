"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError
from datetime import datetime

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


class MessageModelTestCase(TestCase):
    """Test views for messages."""

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

        m = Message(
            text="Sample Text",
            timestamp=datetime.utcnow(),
            user_id=u.id
        )

        db.session.add(m)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(1, Message.query.filter_by(user_id=u.id).count())
        self.assertEqual("Sample Text", u.messages[0].text)

    def test_Message_default_timestamp(self):
        """Does Message.create successfully adds a
        timestamp if not specified?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        m = Message(
            text="Sample test",
            user_id=u.id
        )
        
        db.session.add(m)
        db.session.commit()

        self.assertIsNotNone(m.timestamp)

    def test_user_method(self):
        """Does the user method work as expected?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        m = Message(
            text="Sample Text",
            timestamp=datetime.utcnow(),
            user_id=u.id
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(u.id, m.user.id)
        self.assertEqual(u.username, m.user.username)
        self.assertEqual(u.email, m.user.email)

    def test_Message_create_non_null_text(self):
        """Does Message.create fail to create a new
        message if any of the validations (non-nullable
        fields) fail?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        m = Message(
            timestamp=datetime.utcnow(),
            user_id=u.id
        )

        with self.assertRaises(IntegrityError):
            try:
                db.session.add(m)
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                raise e

        self.assertIsNone(Message.query.filter_by(user_id=u.id).first())

    def test_Message_create_non_null_user_id(self):
        """Does Message.create fail to create a new
        message if any of the validations (non-nullable
        fields) fail?"""

        m = Message(
            text="Sample text"
        )

        with self.assertRaises(IntegrityError):
            try:
                db.session.add(m)
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                raise e

        self.assertEqual(0, Message.query.count())
