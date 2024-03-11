"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


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


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        """Roll back the transaction to keep the database clean. """
        db.session.rollback()

    def test_show_following(self):
        """Can user see the list of people that she's
        following?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.get(f"/users/{self.testuser.id}/following")

            # Make sure it's successful
            self.assertEqual(resp.status_code, 200)

            u = User(email="email@domain.com", username="user_view", password="password")
            db.session.add(u)
            db.session.commit()

            resp = c.get(f"/users/{u.id}/following")

            # Make sure it's successful
            self.assertEqual(resp.status_code, 200)

    def test_not_show_logout(self):
        """When you're logged out, are you disallowed
        from visitn a user's follower/following pages?"""

        with self.client as c:
            with c.session_transaction() as sess:
                if CURR_USER_KEY in sess:
                    del sess[CURR_USER_KEY]

                    resp = c.get(f"/users/1/following")

                    # Make sure it's a redirect
                    self.assertEqual(resp.status_code, 302)

    def test_add_message_logged_in(self):
        """When you're logged in, can you add a message
        as yourself?"""

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
            self.assertEqual(resp.location, f"http://localhost/users/{self.testuser.id}")

            msg = Message.query.one()
            self.assertEqual(self.testuser.id, msg.user.id)

    def test_not_adding_msg_logout(self):
        """When you're logged out, are you disallowed
        from adding messages?"""

        with self.client as c:
            with c.session_transaction() as sess:
                if CURR_USER_KEY in sess:
                    del sess[CURR_USER_KEY]

                    resp = c.post(f"/messages/new", data={"text": "Hello"})

                    # Make sure it's a redirect
                    self.assertEqual(resp.status_code, 302)
                    self.assertEqual(resp.location, f"http://localhost/")

    def test_not_deleting_msg_logout(self):
        """When you're logged out, are you disallowed
        from deleting messages?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess.clear()
                
            resp = c.post("/messages/1/delete")

            # Make sure it's a redirect
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "http://localhost/")

    def test_add_msg_other_user_logged_in(self):
        """When you're logged in, can you add a message
        as another user"""

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
            self.assertEqual(resp.location, f"http://localhost/users/{self.testuser.id}")

            msg = Message.query.one()
            self.assertEqual(self.testuser.id, msg.user.id)