from app import get_db  # required so that the Fakebook objects that map database relations can access the database
from abc import ABC
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class FBObject(ABC):

    def get_dictionary(self):
        pass

    def update_in_db(self):
        pass

"""
User class and related Exceptions
"""
class UserIDNotFoundException(Exception):
    pass

class UserLoginFailedException(Exception):
    pass

class UsernameAlreadyInUseException(Exception):
    pass

class EmailAlreadyInUseException(Exception):
    pass


class User(FBObject):

    def __init__(self, id):

        db = get_db()

        user_data = db.execute("SELECT User.username, User.email, User.first_name, User.surname, User.joined, User.bio, User.dob, Media.file_path, User.last_active, User.profile_pic_id, Media.id FROM User, Media WHERE User.profile_pic_id = Media.id and User.id=?", [id]).fetchone()

        if user_data:
            self.__id = int(id)
            self.__username = user_data['username']
            self.__email = user_data['email']
            self.__first_name = user_data['first_name']
            self.__surname = user_data['surname']
            self.__joined = user_data['joined']
            self.__profile_pic_path = user_data['file_path']
            self.__bio = user_data['bio']
            self.__dob = user_data['dob']
            self.__last_active = user_data['last_active']

        else:
            raise UserIDNotFoundException

    @property
    def id(self):
        return self.__id

    @property
    def username(self):
        return self.__username

    @property
    def first_name(self):
        return self.__first_name

    @property
    def surname(self):
        return self.__surname

    @property
    def joined(self):
        return self.__joined

    @property
    def profile_pic_path(self):
        return self.__profile_pic_path

    @property
    def bio(self):
        return self.__bio

    @property
    def dob(self):
        return self.__dob

    @property
    def last_active(self):
        return self.__last_active

    @property
    def friendships(self):
        return self.get_friendships()

    @property
    def posts(self):
        return self.get_posts()

    @property
    def public_posts(self):
        return self.get_public_posts()

    @staticmethod
    def login_user(email, password):

        # look for user instance in User table with matching email. If found, check their password_hash

        user_row = get_db().execute("SELECT id, email, password_hash FROM User WHERE email=?",[email]).fetchone()

        if user_row and check_password_hash(user_row['password_hash'], password):
            return User(user_row['id'])

        else:
            raise UserLoginFailedException

    @staticmethod
    def register_user(username, email, password, first_name, surname, profile_pic_path, bio, dob):

        db = get_db()
        cur = db.cursor()

        # TODO: Add validation of unique username and email and no required data missing

        # Check whether username exists already
        row = cur.execute("SELECT id FROM User WHERE username=?", [username]).fetchone()
        if row:
            raise UsernameAlreadyInUseException

        # Check whether username exists already
        row = cur.execute("SELECT id FROM User WHERE email=?", [email]).fetchone()
        if row:
            raise EmailAlreadyInUseException


        # Add Media entry for profile pic first

        media_id = None

        if profile_pic_path != "":

            cur.execute("INSERT INTO Media VALUES (NULL, ?)", [profile_pic_path])
            media_id = cur.lastrowid

        # Now add entry to User table

        joined = datetime.utcnow()

        cur.execute("INSERT INTO User VALUES (NULL, ?,?,?,?,?,?,?,?,?,?)", [username, email, generate_password_hash(password), first_name, surname, joined, media_id, bio, dob, str(datetime.utcnow())])

        user_id = cur.lastrowid

        db.commit()

        return User(user_id)

    def __repr__(self):
        return '<User object: {}>'.format(self.id)

    def get_dictionary(self):
        return {
            'id':self.id,
            'username':self.username,
            'first_name':self.first_name,
            'surname':self.surname,
            'joined':self.joined,
            'profile_pic_path':self.profile_pic_path,
            'bio':self.bio,
            'dob':self.dob
        }

    def update_last_active(self, date=None):

        if not date:
            date = str(datetime.utcnow())

        db = get_db()
        db.execute("UPDATE User SET last_active=? WHERE id=?", [date, self.id])
        db.commit()

    def get_posts(self):

        return Post.get_user_posts(self, self)  # Get this User's posts, viewing as themselves (hence all posts)

    def get_friendships(self):

        return Friendship.get_friendships_for_user(self)

    def isFriend(self, other_user):

        return Friendship.verify_friendship(self, other_user)

    def get_public_posts(self):

        return Post.get_user_posts(self)

    def get_posts_as_viewer(self, viewer):

        return Post.get_user_posts(self, viewer)

    def initiate_friendship(self, recipient):

        return Friendship.initiate_friendship(self, recipient)

    def accept_friendship(self, initiator):

        f = Friendship.get_friendship_for_users(self, initiator)

        f.accept(self)

        return f

    def get_friendship_invitations(self):

        # Returns a list of friendships that the user is the recipient of and has not yet accepted.

        waiting_friendships = []

        for f in self.get_friendships():
            if not f.accepted and f.recipient.id == self.id:
                waiting_friendships.append(f)

        return waiting_friendships

    def get_waiting_friendship_invitations(self):

        # Returns a list of friendships that the user has initiated but have not been accepted yet.

        waiting_friendships = []

        for f in self.get_friendships():
            if not f.accepted and f.initiator.id == self.id:
                waiting_friendships.append(f)

        return waiting_friendships


"""
Friendship class and related Exceptions
"""


class FriendshipDoesNotExist(Exception):
    pass


class Friendship(FBObject):

    def __init__(self, id):

        friendship_data = get_db().execute("SELECT * FROM Friendship WHERE id=?", [id]).fetchone()
        self.__id = int(id)
        self.__initator = User(friendship_data['initiator_id'])
        self.__recipient = User(friendship_data['recipient_id'])
        self.__accepted = True if friendship_data['accepted'] == 1 else False
        self.__established_date = friendship_data['established_date']

    @property
    def initiator(self):
        return self.__initator

    @property
    def recipient(self):
        return self.__recipient

    @property
    def accepted(self):
        return self.__accepted

    @property
    def established_date(self):
        return self.__established_date

    @staticmethod
    def verify_friendship(a: User, b: User):

        friendship_data = get_db().execute("SELECT * FROM Friendship WHERE accepted = 1 AND ((initiator_id=? and recipient_id=?) or (initiator_id=? AND recipient_id=?))", [a.id, b.id, b.id, a.id]).fetchone()

        if friendship_data:
            return True
        else:
            return False

    @staticmethod
    def get_friendships_for_user(user: User):

        # Returns a list of all Friendship objects for the specified user, whether accepted or not

        friendships_list = []

        cur = get_db().cursor()

        friendship_rows = cur.execute("SELECT * FROM Friendship WHERE initiator_id=? OR recipient_id=?", [user.id, user.id])

        for row in friendship_rows:

            friendships_list.append(Friendship(row['id']))

        return friendships_list

    def accept(self, recipient: User):

        if self.__recipient.id == recipient.id:  # Only the recipient should be able to accept the friendship
            self.__accepted = True
            self.__established_date = str(datetime.utcnow())
            self.update_in_db()

    def revoke(self, user: User):

        # Need to use id property as the passed User object will not be the same actual object, it will be a new
        # instance populated with the same data as the registered recipient or initiator.

        # Only the recipient or initiator of the Friendship is able to revoke it.

        if self.recipient.id == user.id or self.initiator.id == user.id:

            # TODO: Add code to delete friendship from DB

            db = get_db()

            cur = db.cursor()

            cur.execute("DELETE FROM Friendship WHERE id=?", [self.__id])

            db.commit()

    @staticmethod
    def get_friendship_for_users(a: User, b: User):

        friendship_data = get_db().execute(
            "SELECT id FROM Friendship WHERE (initiator_id=? and recipient_id=?) or (initiator_id=? AND recipient_id=?)",
            [a.id, b.id, b.id, a.id]).fetchone()

        if friendship_data:

            return Friendship(friendship_data['id'])

        else:
            #raise FriendshipDoesNotExist("No Friendship exists between users {} and {}".format(a.id, b.id))
            return None

    @staticmethod
    def initiate_friendship(initiator: User, recipient: User):

        try:

            existing_friendship = Friendship.get_friendship_for_users(initiator, recipient)

            return existing_friendship

        except FriendshipDoesNotExist:

            db = get_db()

            cur = db.cursor()

            cur.execute("INSERT INTO Friendship VALUES (NULL, ?, ?, 0, ?)", [initiator.id, recipient.id, str(datetime.utcnow())])

            friendship_id = cur.lastrowid

            db.commit()

            return Friendship(friendship_id)

    def update_in_db(self):

        db = get_db()

        cur = db.cursor()

        cur.execute("UPDATE Friendship SET accepted=?, established_date=? WHERE id=?", [self.accepted, self.established_date, self.__id])

        db.commit()

    def __repr__(self):
        return "<Friendship object between User {} ({}) and User {} ({}). Friendship accepted: {}, established: {}>"\
            .format(self.initiator.id, self.initiator.username, self.recipient.id, self.recipient.username, self.accepted,
                    self.established_date)

    def __str__(self):
        return "<Friendship object between User {} ({}) and User {} ({}). Friendship accepted: {}, established: {}>"\
            .format(self.initiator.id, self.initiator.username, self.recipient.id, self.recipient.username, self.accepted,
                    self.established_date)


"""
Post class and related exceptions
"""


class PostIDNotFoundException(Exception):
    pass


class Post(FBObject):

    def __init__(self, id):

        db = get_db()

        #post_data = db.execute("SELECT Post.*, Media.file_path FROM Post, Media WHERE Post.media_id = Media.id AND Post.id=?", [id]).fetchone()
        post_data = db.execute(
            "SELECT * FROM Post WHERE id=?", [id]).fetchone()

        if post_data:

            self.__id = int(id)
            self.__text = post_data['text']
            self.__timestamp = post_data['timestamp']
            self.__public = True if post_data['public'] == 1 else False

            self.__media_file_path = None

            media_data = db.execute("SELECT file_path FROM Media WHERE id = ?", [post_data['media_id']]).fetchone()

            if media_data:

                self.__media_file_path = media_data['file_path']

            self.__author = User(post_data['author_id'])
            self.__likes = self.get_likes()
            self.__tagged_users = self.get_tagged_users()


        else:
            raise PostIDNotFoundException

    @property
    def id(self):
        return self.__id

    @property
    def author(self):
        return self.__author

    @property
    def text(self):
        return self.__text

    @property
    def media_file_path(self):
        return self.__media_file_path

    @property
    def timestamp(self):
        return self.__timestamp

    @property
    def public(self):
        return self.__public

    @property
    def likes(self):
        return self.__likes

    @property
    def likes_count(self):
        return len(self.__likes)

    @property
    def tagged_users(self):
        return self.__tagged_users

    def get_likes(self):
        """
        :return: a list of Users who have liked the post
        """

        cur = get_db().cursor()

        like_rows = cur.execute("SELECT user_id FROM PostLike WHERE post_id=?", [self.id]).fetchall()

        like_users = []

        for row in like_rows:
            like_users.append(User(row['user_id']))

        return like_users

    def get_tagged_users(self):
        """
        :return: a list of users that are tagged in this Post
        """

        tagged_users = []  # initialise empty list

        cur = get_db().cursor()

        tag_rows = cur.execute("SELECT tagged_user_id FROM Tag WHERE post_id=?", [self.id]).fetchall()

        for row in tag_rows:
            tagged_users.append(User(row['tagged_user_id']))

        return tagged_users

    def user_is_tagged(self, user):

        return user in self.__tagged_users


    @staticmethod
    def get_tagged_posts_for_user(user: User):

        """
        :param user: A User object for whom tagged posts are to be retrieved
        :return: A list of Post objects that user is tagged in
        """

        tagged_posts = []

        cur = get_db().cursor()

        post_rows = cur.execute("SELECT post_id FROM Tag WHERE tagged_user_id=?", [user.id]).fetchall()

        for row in post_rows:

            tagged_posts.append(Post(row['post_id']))

        return tagged_posts

    @staticmethod
    def get_user_posts(user: User, viewer: User = None):
        """
        :param user: A User object that represents the author of posts to be returned;
        :param viewer: A User object that represents the viewer. Only viewers that are friends with the author can see non-public posts.
        :return: A list of Posts authored by user
        """
        user_posts = []

        cur = get_db().cursor()

        user_post_rows = cur.execute("SELECT id, public, author_id FROM Post WHERE author_id=?", [user.id]).fetchall()

        for row in user_post_rows:

            # If the post is public or if the viewer is the author of the post

            if row['public'] == 1 or (viewer and row['author_id'] == int(viewer.id)):

                user_posts.append(Post(row['id']))

            elif viewer and viewer.isFriend(user):

                user_posts.append(Post(row['id']))

        return user_posts
