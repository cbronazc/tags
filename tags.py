from flask import Flask, jsonify, request, render_template
import requests
import json
from operator import itemgetter
from werkzeug.contrib.cache import SimpleCache
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask.ext.migrate import Migrate
from flask.ext.script import Manager

app = Flask(__name__)

CACHE_TIMEOUT = 500
cache = SimpleCache()

db = SQLAlchemy()
db.init_app(app)
migrate = Migrate()
migrate.init_app(app, db)
manager = Manager(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root@localhost/tags"


tags = db.Table('tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'))
)


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    subscribed = db.Column(db.String(255))
    articles = db.relationship('Article', secondary=tags,
        backref=db.backref('tags', lazy='dynamic'))


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    headline = db.Column(db.String(255), unique=True)
    subhead = db.Column(db.String(255))
    url = db.Column(db.String(255))
    photo = db.Column(db.String(255))


def get_data():
    key_prefix='articles'
    if cache.get(key_prefix):
        print "from cache"
        return cache.get(key_prefix)
    else:
        print "from live"
        data = requests.get("http://www.azcentral.com/home.json")
        data = json.loads(data.content)
        cache.set(key_prefix, data)
        return data


def process_data():
    data = get_data()
    articles = []
    for d in data.get('topfullwide')[0].get('contents'):
        headline = d.get('headline')
        attrs = d.get('attrs')
        if headline and attrs:
            subhead = attrs.get('subhead') if attrs.get('subhead') else attrs.get('metadescription')
            photo = d.get('photo').get('crops').get('4_3')
            url = "http://azcentral.com" + d.get('pageurl').get('Text') if d.get('pageurl').get('Text') else None
            keywords = attrs.get('keywords').split(",")
        if headline and subhead and photo and url:

            # create article
            if not Article.query.filter(Article.headline==headline).first():
                db.session.add(Article(headline=headline, subhead=subhead, photo=photo, url=url))
            # create tags
            for word in keywords:
                if Tag.query.filter(Tag.name==word).count() < 1:
                    db.session.add(Tag(name=word))
            db.session.commit()

            article = Article.query.filter(Article.headline==headline).first()
            if article:
                # find tags and append to the many-to-many table
                for word in keywords:
                    tag = Tag.query.filter(Tag.name==word).first()
                    if tag not in article.tags:
                        article.tags.append(tag)
                db.session.commit()


@app.route('/')
def index():
    process_data()
    data = []
    subbed = Tag.query.filter(Tag.subscribed==1).all()
    for sub in subbed:
        for article in sub.articles:
            if article not in data:
                data.append(article)
    tags = Tag.query.order_by(func.rand()).all()
    return render_template('index.html', data=data, tags=tags)



@app.route('/sub', methods=['POST'])
def sub():
    name = request.form.get('name').strip()
    tag = Tag.query.filter(Tag.name==name).first()
    if tag:
        tag.subscribed = '0' if tag.subscribed == '1' else '1'
        db.session.add(tag)
        db.session.commit()
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5010)