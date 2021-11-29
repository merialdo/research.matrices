from flask import Flask
from flask_restful import Api
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from resources.routes import initialize_routes
from resources.errors import errors
from database.db import initialize_db


# init flask application
app = Flask(__name__)

# enable Cross Origin Resource Sharing (CORS)
CORS(app)

# database setting (conf)
app.config['MONGODB_SETTINGS'] = {
    'host' : 'mongodb://localhost/HTR'
}
# jwt secret (conf)
app.config['JWT_SECRET_KEY'] = 't1NP63m4wnBg6nyHYKfmc2TpCOGI4nss'

# init Flask Restful Api
api = Api(app, errors = errors)

# init JWT token manager
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# initi db and routes
initialize_db(app)
initialize_routes(api)

app.run(debug=True)


# how to run:
# conda create -n "htr" python=3.8.0
# conda activate htr
# pip install -r requirements.txt
# python app.py
