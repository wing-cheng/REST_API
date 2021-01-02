from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_mail import Mail, Message
from sqlalchemy import Column, Integer, String, Float, ForeignKeyConstraint, PrimaryKeyConstraint
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///planetsapi'
app.config['JWT_SECRET_KEY'] = 'Coding Expert'
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print("Database Created!")


@app.cli.command('db_drop')
def db_drop():
    db.session.remove()
    db.drop_all()
    print("Database Dropped!")


@app.cli.command('db_seed')
def db_seed():

    mercury = Planets(
        pname='Mercury',
        pclass='D',
        mass=3.258e23,
        radius=1516,
        distance=35.98e6
    )

    venus = Planets(
        pname='Venus',
        pclass='K',
        mass=4.867e24,
        radius=3760,
        distance=67.24e6 
    )

    earth = Planets(
        pname='Earth',
        pclass='M',
        mass=5.972e24,
        radius=3969,
        distance=92.96e6 
    )

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    tom = Users(
        first_name='Tom',
        last_name='John',
        email='hello@hello.com',
        password='paSSworD',
        planet_id=3
    )

    db.session.add(tom)
    

    home_star1 = Homestar(
        home=3,
        star=1
    )

    home_star2 = Homestar(
        home=3,
        star=2
    )
    db.session.add(home_star1)
    db.session.add(home_star2)
    db.session.commit()
    print('Database Seeded!')


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/super_simple')
def super_simple():
    return jsonify(message='Hello from the Planetary API.'), 200


@app.route('/not_found')
def not_found():
    return jsonify(message='That resource was not found'), 404


@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))
    if age < 18:
        return jsonify(message="Sorry " + name + ", you are not old enough."), 401
    else:
        return jsonify(message="Welcome " + name + ", you are old enough!")


@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
    if age < 18:
        return jsonify(message="Sorry " + name + ", you are not old enough."), 401
    else:
        return jsonify(message="Welcome " + name + ", you are old enough!")


@app.route('/planets', methods=['GET'])
def planets():
    planets_list = Planets.query.all()
    # json-serialize planets_list
    result = planets_schema.dump(planets_list)
    return jsonify(data=result)


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    first_name = request.form['first_name']
    test_email = Users.query.filter_by(email=test_email).first()
    if test_email:
        return jsonify(message='Email address already registered!'), 409
    
    test_first_name = Users.query.filter_by(first_name=test_first_name).first()
    if test_first_name:
        return jsonify(message="First name already registered!"), 409

    # get the registration info and make a new user obj
    new_user = Users(
        first_name=first_name,
        last_name=request.form['last_name'],
        password=request.form['password'],
        email=email,
        planet_id=None
    )
    planet_id = request.form['planet_id']
    if planet_id:
        new_user['planet_id'] = planet_id
    # add the new user to database 
    db.session.add(new_user)
    db.session.commit()
    return jsonify(message='User Created Successfully!'), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']
    
    test = Users.query.filter_by(email=email, password=password).first()
    if test:
        token = create_access_token(identity=test.id)
        return jsonify(message='Login succeeded!', access_token=token)
    else:
        return jsonify(message='Unregistered email or incorrect password'), 401


@app.route('/get_pw', methods=['GET'])
@jwt_required
def get_pw():

    current_user = get_jwt_identity()

    test_user_exists = Users.query.filter_by(id=current_user).with_entities(
        Users.password,
        Users.email
    ).first()
    if not test_user_exists:
        return jsonify(message='User not exist'), 401

    msg = Message(
        'Your planetary password is ' + test_user_exists.password,
        sender='admin@planetary-api.com',
        recipients=[test_user_exists.email]
    )
    mail.send(msg)
    return jsonify(message='Password sent to ' + test_user_exists.email)



@app.route('/planet_detail/<int:pid>', methods=['GET'])
def planet_detail(pid: int):
    test_planet_exists = Planets.query.filter_by(pid=pid).first()
    if test_planet_exists:
        result = planet_schema.dump(test_planet_exists)
        return jsonify(data=result)
    else:
        return jsonify(message="Planet does not exist"), 404



@app.route('/add_planet', methods=['POST'])
@jwt_required
def add_planet():
    # get the new planet name
    pname = request.form['pname']
    test_planet_exists = Planets.query.filter_by(pname=pname).first()
    if test_planet_exists:
        return jsonify(message=f"Planet {pname} already exists"), 409
    
    ptype = request.form['ptype']
    home_star = request.form['home_star']
    mass = float(request.form['mass'])
    radius = float(request.form['radius'])
    distance = float(request.form['distance'])
    new_planet = Planets(
        pname=pname,
        ptype=ptype,
        mass=mass,
        distance=distance,
        radius=radius,
        home_star=home_star
    )

    db.session.add(new_planet)
    db.session.commit()
    return jsonify(message="New planet added successfuly!")



@app.route('/update_planet', methods=['PUT'])
@jwt_required
def update_planet():
    pid = int(request.form['pid'])
    test_planet = Planets.query.filter_by(pid=pid).first()
    if test_planet:
        test_planet.pname = request.form['pname']
        test_planet.ptype = request.form['ptype']
        test_planet.home_star = request.form['home_star']
        test_planet.mass = float(request.form['mass'])
        test_planet.radius = float(request.form['radius'])
        test_planet.distance = float(request.form['distance'])
        db.session.commit()
        return jsonify(message='Planet updated successfully!'), 202

    return jsonify(message='Planet does not exist'), 404



@app.route('/remove_planet', methods=['DELETE'])
@jwt_required
def remove_planet():
    pid = int(request.form['pid'])
    test_planet = Planets.query.filter_by(pid=pid).first()
    if test_planet:
        db.session.delete(test_planet)
        db.session.commit()
        return jsonify(message='Planet deleted'), 202
    return jsonify(message='Planet does not exist'), 404



@app.route('/user_detail/<int:uid>', methods=['GET'])
@jwt_required
def user_detail(uid: int):
    
    current_user = get_jwt_identity()
    detail = Users.query.filter_by(id=uid).with_entities(
        Users.first_name,
        Users.last_name,
        Users.email,
        Users.id,
        Users.planet_id
    ).first()

    # if there does not exist user with the given user id
    if not detail:
        return jsonify(message="Not exist such user with given user id"), 404

    planet = Planets.query.filter_by(pid=detail.planet_id).with_entities(Planets.pname).first()
    planet_name = None
    if planet_name:
        planet_name = planet.pname
    # if current user is retrieving its own detail
    if current_user == uid:
        result = {
            "first_name": detail.first_name,
            "last_name": detail.last_name,
            "email": detail.email,
            "user_id": uid,
            "planet": planet_name
        }
    else:
        # else a user retrieving other's detail
        # can only retrieve first_name, user_id and planet_id
        result = {
            "first_name": detail.first_name,
            "user_id": uid,
            "planet": planet_name
        }

    return jsonify(message="The following is your account detail" ,data=result)
    


@app.route('/user_migrate/<int:pid>', methods=["POST"])
@jwt_required
def user_migrate(pid:int):
    # this func allows current user to change the living planet
    # or to choose one planet to live if he/she does not have one

    # check if planet exists
    test_planet_exists = Planets.query.filter_by(pid=pid).first()
    if not test_planet_exists:
        return jsonify(message="Not exist such planet with given planet id"), 404

    current_user = get_jwt_identity()
    Users.query.filter_by(id=current_user).update({'planet_id': pid})
    db.session.commit()
    return jsonify(message=f"You migrated to planet {test_planet_exists.pname}! (planet id: {pid})")


@app.route('/new_planet', methods=['POST'])
@jwt_required
def new_planet():
    current_user = get_jwt_identity()

    # this func serves for a user discovering a new planet
    # and add a new planet to the datebase with the given planet info
    new = Planets(
        pname=request.form['planet_name'],
        pclass=request.form['planet_class'],
        radius=float(request.form['radius']),
        mass=float(request.form['mass']),
        distance=float(request.form['distance']),
        owner=current_user
    )
    db.session.add(new)
    db.session.commit()

    return jsonify(message="You discovery has been recorded!")



### database models
class Users(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String, unique=True)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    planet_id = Column(Integer, nullable=True)
    ForeignKeyConstraint(['planet_id'], ['Planets.pid'], name="planet_people", onupdate="CASCADE", ondelete="SET NULL")
    

class Planets(db.Model):
    __tablename__ = 'planets'
    pid = Column(Integer, primary_key=True)
    pname = Column(String, unique=True)
    pclass = Column(String(1))
    mass =  Column(Float)
    radius = Column(Float)
    distance = Column(Float)
    owner = Column(Integer)
    ForeignKeyConstraint(['owner'], ['Users.id'], name="planet_ownership", onupdate="CASCADE", ondelete="SET NULL")


class Homestar(db.Model):
    __tablename__ = "homestar"
    home = Column(Integer, primary_key=True)
    star = Column(Integer, primary_key=True)
    ForeignKeyConstraint(['home'], ['Planets.pid'], name="home_planet", onupdate="CASCADE", ondelete="SET NULL")
    ForeignKeyConstraint(['star'], ['Planets.pid'], name="homestar_planet", onupdate="CASCADE", ondelete="SET NULL")
###


class User_schema(ma.Schema):
    class Meta:
        fields = ('id', 'firstname', 'last_name', 'email', 'password')
 
class Planet_schema(ma.Schema):
    class Meta:
        fields = ('pid', 'pname', 'ptype', 'home_star', 'mass', 'radius', 'distance')

class Homestar_schema(ma.Schema):
    class Meta:
        fields = ('home', 'star')

user_schema = User_schema()
planet_schema = Planet_schema()
planets_schema = Planet_schema(many=True)
homestar_schema = Homestar_schema()


if __name__ == '__main__':
    app.run(port=5000, debug=True)
    