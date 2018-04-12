from app import app
from app.fb_objects import Post, User, Friendship


@app.route('/post_test/<id>')
def post_test(id):

    post = Post(id)

    return "Post test complete"

@app.route('/user_posts_test/<id>')
def user_posts_test(id):

    user_posts = User(id).get_posts()

    return "User post test complete: {}".format(len(user_posts))

@app.route('/user_posts_as_user_test/<user_id>/<viewer_id>')
def user_posts_as_user_test(user_id, viewer_id):

    user_posts = Post.get_user_posts(User(user_id), User(viewer_id))

    return str(len(user_posts))

@app.route('/tagged_users_test/<post_id>')
def tagged_users_test(post_id):

    tagged_users = Post(post_id).tagged_users

    return "Tagged user test copmlete"

@app.route('/verify_friendship_test/<a>/<b>')
def verify_friendship_test(a, b):

    return str(User(a).isFriend(User(b)))

@app.route('/get_friendships_for_user_test/<user_id>')
def get_friendships_for_user_test(user_id):

    friendships = User(user_id).friendships

    return str(len(friendships))

@app.route('/initiate_friendship_test/<user_id>/<recipient_id>')
def initiate_friendship_test(user_id, recipient_id):

    new_friendship = User(user_id).initiate_friendship(User(recipient_id))

    return "Test complete"

@app.route('/accept_friendship_test/<recipient_id>/<initiator_id>')
def accept_friendship_test(recipient_id, initiator_id):

    f = Friendship.get_friendship_for_users(User(recipient_id), User(initiator_id))

    f.accept(User(recipient_id))

    return "Test complete"

@app.route('/revoke_friendship_test/<a>/<b>')
def revoke_friendship_test(a, b):

    f = Friendship.get_friendship_for_users(User(a), User(b))

    f.revoke(User(a))

    return "Test complete"

@app.route('/get_invitations_test/<user_id>')
def get_invitations_test(user_id):

    waiting_friendships = User(user_id).get_friendship_invitations()

    return str(len(waiting_friendships))

@app.route('/get_waiting_invitations_test/<user_id>')
def get_waiting_invitations_test(user_id):

    waiting_friendships = User(user_id).get_waiting_friendship_invitations()

    return str(len(waiting_friendships))