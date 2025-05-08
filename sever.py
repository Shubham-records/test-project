from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/chat')
def chat():
    return render_template('chat.html')

if __name__ == '__main__':
    app.run(debug=True)
