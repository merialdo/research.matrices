from controller import *


def initialize_routes(api):
    # add new routes to get / add / delete / update datasets
    api.add_resource(DatasetsController, '/api/datasets')
    api.add_resource(DatasetController, '/api/datasets/<id>')  # id of dataset
    api.add_resource(DatasetExportController, '/api/dataset-creator')  # temporary route for materializing dataset

    # not really used yet
    api.add_resource(DatasetImageController, '/api/datasets/getimage/<id_ds>/<id_img>')  # id of dataset
    api.add_resource(ModelsController, '/api/models')
    api.add_resource(ModelController, '/api/models/<id>')

