from flask import Flask, render_template, send_file
from alx_scrape_app.alx_scrape_view import alx_scrape_view

app = Flask(__name__)
app.register_blueprint(alx_scrape_view, url_prefix="")


@app.route("/")
def home():
    return "<h1>Home!</h1>"

@app.route("/download/<file>")
def download(file):
    return send_file(file, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
