from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from collections import defaultdict

bp = Blueprint('userview', __name__, url_prefix='/user')

@bp.route('/<username>', methods=('GET',))
def viewUser(username):
	db = get_db(dict_factory=True)
	userId = db.execute("SELECT id FROM user WHERE username = ?",(username,)).fetchone()['id']
	user = {'username':username, 'id':userId}
	# Get all comments that user has madeon
	comments = db.execute("SELECT p.title, c.postId, c.commentContent, c.createdAt FROM commentsOnPost c JOIN post p ON c.postId=p.id WHERE c.author_id=? ORDER BY c.createdAt DESC", (userId,)).fetchall()

	return render_template('userview/view.html', user=user, comments=comments)