class InternalServerException(Exception):
    pass


class SchemaValidationException(Exception):
    pass


class ObjectAlreadyExistsException(Exception):
    pass


class UpdatingModelException(Exception):
    pass


class DeletingModelException(Exception):
    pass


class ObjectDoesNotExistException(Exception):
    pass


class EmailAlreadyExistsException(Exception):
    pass


class UnauthorizedException(Exception):
    pass


exceptions = {
    "InternalServerException": {
        "message": "Something went wrong",
        "status": 500
    },

    "SchemaValidationException": {
        "message": "Request is missing required fields",
        "status": 400
    },

    "ObjectAlreadyExistsException": {
        "message": "An Object with passed identiier already exists",
        "status": 400
    },

    "UpdatingModelException": {
        "message": "Updating Model added by other is forbidden",
        "status": 403
    },

    "DeletingModelException": {
        "message": "Deleting Model added by other is forbidden",
        "status": 403
    },

    "ObjectDoesNotExistException": {
        "message": "Object with given id doesn't exists",
        "status": 400
    },

    "EmailAlreadyExistsException": {
        "message": "User with given email address already exists",
        "status": 400
    },

    "UnauthorizedException": {
        "message": "Invalid username or password",
        "status": 401
    }
}
