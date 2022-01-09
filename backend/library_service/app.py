from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from routes import initialize_routes
from errors import errors
from database import initialize_db
from config import MONGODB_HOST

# init flask application
app = Flask(__name__)

# enable Cross Origin Resource Sharing (CORS)
CORS(app)

# database setting (conf)
app.config['MONGODB_SETTINGS'] = {'host': MONGODB_HOST}

# initialize Flask Restful Api
api = Api(app, errors=errors)

# initialize db and routes
initialize_db(app)
initialize_routes(api)

# launch application
app.run(debug=True)
