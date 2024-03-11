"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 8989
        self.testuser.id = self.testuser_id
        db.session.commit()

    def tearDown(self):
        """Roll back the transaction to keep the database clean. """
        db.session.rollback()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_show_message(self):
        """Can message(s) be shown to the user?"""

        u = User(email="t@test.com", username="username", password="password")
        db.session.add(u)
        db.session.commit()
        
        msg = Message(text="Hello", user_id=u.id)
        db.session.add(msg)
        db.session.commit()

        resp = self.client.post(f"/messages/{msg.id}/delete")

        self.assertEqual(resp.status_code, 302)

    def test_delete_message(self):
        """Can message(s) be deleted by the user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
        msg = Message(text="Botafgo!!", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        # Check if the message is in the database before deletion
        self.assertIsNotNone(Message.query.filter_by(user_id=self.testuser.id).first())

        resp = c.post(f"/messages/{msg.id}/delete")

        self.assertEqual(resp.status_code, 302)

        self.assertIsNone(Message.query.filter_by(user_id=self.testuser.id).first())
        self.assertEqual(self.testuser.id, msg.user.id)

    def test_message_delete_no_authentication(self):

        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser_id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(1234)
            self.assertIsNotNone(m)