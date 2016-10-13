from flask import Flask, Response, redirect, url_for, request, session, abort
from flask_login import LoginManager, UserMixin, \
                                login_required, login_user, logout_user 
import json

app = Flask(__name__)

# config
app.config.update(
    DEBUG = True,
    SECRET_KEY = 'secret_xxx'
)

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

conf = json.load(open("config.json"))

class User(UserMixin):

    def __init__(self, id):
        self.id = id
        self.name = conf["username"]
        self.password = conf["password"]
        
    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password)


users = [User(1)]


# some protected url
@app.route('/')
@login_required
def home():
    return Response("Hello World!")

 
# somewhere to login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']        
        if password == conf["password"] and username == conf["username"]:
            id = 1
            user = User(id)
            login_user(user)
            return redirect(request.args.get("next"))
        else:
            return abort(401)
    else:
        return Response('''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
        ''')


# somewhere to logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return Response('<p>Logged out</p>')


# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')
    
    
# callback to reload the user object        
@login_manager.user_loader
def load_user(userid):
    return User(userid)
    

if __name__ == "__main__":
    app.run('0.0.0.0')

