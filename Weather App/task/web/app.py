from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import sys
import requests
import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/weather.db'
app.config.update(SECRET_KEY=os.urandom(24))
db = SQLAlchemy(app)
cities, city_id = [], 0


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)


# to clear database
for query in City.query.all():
    db.session.delete(query)
    db.session.commit()


def get_weather(city):
    global city_id
    with open('weather_api', 'r') as file:
        api_key = file.read().rstrip('\n')
    r = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}")
    if r:
        state = r.json()['weather'][0]['main']
        temp = int(r.json()['main']['temp'])
        temp = round((temp - 273.15), 2)  # the api gives temperature in kelvin
        city_id = r.json()['id']
        hour = (datetime.datetime.utcnow() + datetime.timedelta(seconds=r.json()['timezone'])).hour
        if hour in range(17, 24):
            time = "card evening-morning"
        elif hour in range(6, 17):
            time = "card day"
        else:
            time = "card night"
        return {'city_name': city, 'degrees': temp, 'state': state, 'card': time, 'id': city_id}


@app.route('/')
def index():
    db.create_all()
    list_city = []
    for city in City.query.all():
        city = city.name
        list_city.insert(0, get_weather(city))
    return render_template('index.html', weather=list_city)


@app.route('/add', methods=['POST', 'GET'])
def add():
    global city_id
    if request.method == 'POST':
        city = request.form['city_name']
        if get_weather(city) and (city in cities):
            print('The city has already been added to the list!')
            flash('The city has already been added to the list!')
        elif get_weather(city) and (city not in cities):
            print('Adding -' + city)
            print(get_weather(city))
            cities.append(city)
            city_id = get_weather(city)['id']
            city_to_db = City(id=city_id, name=city)
            db.session.add(city_to_db)
            db.session.commit()
        else:
            flash("The city doesn't exist!")
            print("The city doesn't exist!")
        return redirect('/')


@app.route('/delete', methods=['GET', 'POST'])
def delete():
    global city_id
    if request.method == 'POST':
        city = City.query.filter_by(id=city_id).first()
        db.session.delete(city)
        db.session.commit()
        return redirect('/')


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
