from flask import Response, request
from database.models import Model
from flask_restful import Resource

from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist, \
ValidationError, InvalidQueryError
from resources.errors import SchemaValidationError, ModelAlreadyExistsError, \
InternalServerError, UpdatingModelError, DeletingModelError, ModelNotExistsError

# class to handle  get and post operations on model collection
class ModelsApi(Resource):

    # get the collection of models
    def get(self):
        try:
            models = Model.objects.to_json()
            return Response(models, mimetype="application/json", status=200)
        except DoesNotExist:
            raise ModelNotExistsError
        except Exception:
            raise InternalServerError
    
    # add a new model to model collection
    def post(self):
        try:
            body = request.get_json()
            model = Model(**body)
            model.save()
            id = model.id
            return {'id': str(id)}, 200
        except (FieldDoesNotExist, ValidationError):
            raise SchemaValidationError
        except NotUniqueError:
            raise ModelAlreadyExistsError
        except Exception as e:
            raise InternalServerError


# class to handle get,put,delete operations on model
class ModelApi(Resource):

    def get(self,id):
        try:
            model = Model.objects.get(id=id).to_json()
            return Response(model, mimetype='application/json', status=200)
        except DoesNotExist:
            raise DeletingModelError
        except Exception:
            raise InternalServerError

    # update a stored model
    def put(self, id):
        try:
            body = request.get_json()
            Model.objects.get(id=id).update(**body)
            return 'updated model '+str(id), 200
        except InvalidQueryError:
             raise SchemaValidationError
        except DoesNotExist:
             raise UpdatingModelError
        except Exception:
             raise InternalServerError 

    # delete a stored model
    def delete(self, id):
        try:
            model = Model.objects.get(id=id)
            model.delete()
            return 'deleted model '+str(id), 200
        except DoesNotExist:
            raise DeletingModelError
        except Exception:
            raise InternalServerError