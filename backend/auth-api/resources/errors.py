
class InternalServerError(Exception):
    pass

class SchemaValidationError(Exception):
    pass

class ModelAlreadyExistsError(Exception):
    pass

class UpdatingModelError(Exception):
    pass

class DeletingModelError(Exception):
    pass

class ModelNotExistsError(Exception):
    pass

class EmailAlreadyExistsError(Exception):
    pass

class UnauthorizedError(Exception):
    pass

errors = {
    "InternalServerError": {
        "message": "Something went wrong",
        "status": 500
    },
     "SchemaValidationError": {
         "message": "Request is missing required fields",
         "status": 400
     },
     "ModelAlreadyExistsError": {
         "message": "Model with given name already exists",
         "status": 400
     },
     "UpdatingModelError": {
         "message": "Updating Model added by other is forbidden",
         "status": 403
     },
     "DeletingModelError": {
         "message": "Deleting Model added by other is forbidden",
         "status": 403
     },
     "ModelNotExistsError": {
         "message": "Model with given id doesn't exists",
         "status": 400
     },
     "EmailAlreadyExistsError": {
         "message": "User with given email address already exists",
         "status": 400
     },
     "UnauthorizedError": {
         "message": "Invalid username or password",
         "status": 401
     }
}