from flask import Flask, request, redirect, url_for
from db import init_db, create_account, verify_account, add_profile, get_profiles_by_user, update_profile, delete_profile, get_profile_by_id

app = Flask(__name__)

init_db()

current_user = {}

@app.route('/', methods=['GET'])
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
      <title>Password Manager</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 50px; }
        a { display: inline-block; margin: 10px; text-decoration: none; }
      </style>
    </head>
    <body>
      <h2>Welcome to the Password Manager</h2>
      <a href="/login">Login</a>
      <a href="/create_account">Create Account</a>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return "Missing username or password", 400
        success, account_id, account_key = verify_account(username, password)
        if success:
            global current_user
            current_user = {"id": account_id, "username": username, "key": account_key}
            return redirect(url_for('profiles'))
        else:
            return '''
                <!DOCTYPE html>
                <html>
                <head>
                  <title>Login Error</title>
                </head>
                <body>
                  <h2>Login Error</h2>
                  <p>Invalid credentials or account does not exist.</p>
                  <a href="/login">Try again</a>
                </body>
                </html>
            '''
    else:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
          <title>Login</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 50px; }
            form { max-width: 300px; margin: auto; }
            label, input { display: block; width: 100%; margin-bottom: 10px; }
          </style>
        </head>
        <body>
          <h2>Login</h2>
          <form method="POST">
            <label for="username">Username (email):</label>
            <input type="text" id="username" name="username" required>
            
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required>
            
            <button type="submit">Login</button>
          </form>
          <a href="/">Back to Home</a>
        </body>
        </html>
        '''

@app.route('/create_account', methods=['GET', 'POST'])
def create_account_route():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return "Missing username or password", 400
        success, account_id, account_key = create_account(username, password)
        if success:
            global current_user
            current_user = {"id": account_id, "username": username, "key": account_key}
            return redirect(url_for('profiles'))
        else:
            return '''
                <!DOCTYPE html>
                <html>
                <head>
                  <title>Create Account Error</title>
                </head>
                <body>
                  <h2>Create Account Error</h2>
                  <p>An account with that username already exists.</p>
                  <a href="/create_account">Try again</a>
                </body>
                </html>
            '''
    else:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
          <title>Create Account</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 50px; }
            form { max-width: 300px; margin: auto; }
            label, input { display: block; width: 100%; margin-bottom: 10px; }
          </style>
        </head>
        <body>
          <h2>Create Account</h2>
          <form method="POST">
            <label for="username">Username (email):</label>
            <input type="text" id="username" name="username" required>
            
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required>
            
            <button type="submit">Create Account</button>
          </form>
          <a href="/">Back to Home</a>
        </body>
        </html>
        '''

@app.route('/profiles', methods=['GET'])
def profiles():
    if not current_user:
        return redirect(url_for('home'))
    user_profiles = get_profiles_by_user(current_user["id"], current_user["key"])
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
      <title>Profiles</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 50px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        a, button { margin-right: 5px; text-decoration: none; }
        /* CSS classes for password strength */
        .strength-weak { color: red; font-weight: bold; }
        .strength-acceptable { color: orange; font-weight: bold; }
        .strength-strong { color: green; font-weight: bold; }
      </style>
    </head>
    <body>
      <h2>Your Profiles</h2>
      <a href="/profile/new"><button>Add New Profile</button></a>
      <table>
        <tr>
          <th>Name</th>
          <th>Username</th>
          <th>Password</th>
          <th>Strength</th>
          <th>Expiration Date</th>
          <th>Actions</th>
        </tr>
    '''
    for profile in user_profiles:
        strength_class = ""
        if profile['strength'] == "Weak":
            strength_class = "strength-weak"
        elif profile['strength'] == "Acceptable":
            strength_class = "strength-acceptable"
        elif profile['strength'] == "Strong":
            strength_class = "strength-strong"
            
        html += f'''
        <tr>
          <td>{profile['name']}</td>
          <td>{profile['username']}</td>
          <td>{profile['password']}</td>
          <td class="{strength_class}">{profile['strength']}</td>
          <td>{profile['expires'] if profile['expires'] else ""}</td>
          <td>
            <a href="/profile/edit/{profile['id']}"><button>Edit</button></a>
            <a href="/profile/delete/{profile['id']}"><button>Delete</button></a>
          </td>
        </tr>
        '''
    html += '''
      </table>
    </body>
    </html>
    '''
    return html

@app.route('/profile/new', methods=['GET', 'POST'])
def new_profile():
    if not current_user:
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form.get('name')
        prof_username = request.form.get('username')
        prof_password = request.form.get('password')
        expires = request.form.get('expires')
        add_profile(current_user["id"], name, prof_username, prof_password, expires, current_user["key"])
        return redirect(url_for('profiles'))
    else:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
          <title>Add New Profile</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 50px; }
            form { max-width: 400px; margin: auto; }
            label, input { display: block; width: 100%; margin-bottom: 10px; }
          </style>
        </head>
        <body>
          <h2>Add New Profile</h2>
          <form method="POST">
            <label for="name">Profile Name:</label>
            <input type="text" id="name" name="name" required>
            
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" required>
            
            <label for="password">Password:</label>
            <input type="text" id="password" name="password" required>
            
            <label for="expires">Expiration Date:</label>
            <input type="date" id="expires" name="expires">
            
            <button type="submit">Add Profile</button>
          </form>
          <a href="/profiles">Back to Profiles</a>
        </body>
        </html>
        '''

@app.route('/profile/edit/<int:profile_id>', methods=['GET', 'POST'])
def edit_profile_route(profile_id):
    if not current_user:
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form.get('name')
        prof_username = request.form.get('username')
        prof_password = request.form.get('password')
        expires = request.form.get('expires')
        update_profile(profile_id, current_user["id"], name, prof_username, prof_password, expires, current_user["key"])
        return redirect(url_for('profiles'))
    else:
        profile = get_profile_by_id(profile_id, current_user["id"], current_user["key"])
        if profile is None:
            return "Profile not found", 404
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
          <title>Edit Profile</title>
          <style>
            body {{ font-family: Arial, sans-serif; margin: 50px; }}
            form {{ max-width: 400px; margin: auto; }}
            label, input {{ display: block; width: 100%; margin-bottom: 10px; }}
          </style>
        </head>
        <body>
          <h2>Edit Profile: {profile['name']}</h2>
          <form method="POST">
            <label for="name">Profile Name:</label>
            <input type="text" id="name" name="name" value="{profile['name']}" required>
            
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" value="{profile['username']}" required>
            
            <label for="password">Password:</label>
            <input type="text" id="password" name="password" value="{profile['password']}" required>
            
            <label for="expires">Expiration Date:</label>
            <input type="date" id="expires" name="expires" value="{profile['expires'] if profile['expires'] else ''}">
            
            <button type="submit">Update Profile</button>
          </form>
          <a href="/profiles">Back to Profiles</a>
        </body>
        </html>
        '''

@app.route('/profile/delete/<int:profile_id>', methods=['GET', 'POST'])
def delete_profile_route(profile_id):
    if not current_user:
        return redirect(url_for('home'))
    if request.method == 'POST':
        delete_profile(profile_id, current_user["id"])
        return redirect(url_for('profiles'))
    else:
        profile = get_profile_by_id(profile_id, current_user["id"], current_user["key"])
        if profile is None:
            return "Profile not found", 404
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
          <title>Delete Profile</title>
          <style>
            body {{ font-family: Arial, sans-serif; margin: 50px; }}
          </style>
        </head>
        <body>
          <h2>Delete Profile: {profile['name']}</h2>
          <p>Are you sure you want to delete this profile?</p>
          <form method="POST">
            <button type="submit">Yes, Delete</button>
          </form>
          <a href="/profiles">Cancel</a>
        </body>
        </html>
        '''

if __name__ == '__main__':
    app.run(debug=True)
