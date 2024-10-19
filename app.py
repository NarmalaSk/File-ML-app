from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "bumblebee"
@app.route('/login')
def login():
    printf("login page")
    return "index"
if __name__ == "__main__":
    app.run(debug=True)
