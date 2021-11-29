from flask import Response, request
from database.models import Model, User
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist, \
    ValidationError, InvalidQueryError
from resources.errors import SchemaValidationError, ModelAlreadyExistsError, \
    InternalServerError, UpdatingModelError, DeletingModelError, ModelNotExistsError


# class to handle get operations on user
class UserApi(Resource):

    @jwt_required()
    def get(self, id):
        try:
            user = User.objects.get(id=id).to_json()
            return Response(user, mimetype='application/json', status=200)
        except DoesNotExist:
            raise InternalServerError
        except Exception:
            raise InternalServerError
