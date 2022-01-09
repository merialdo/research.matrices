from controller import *


def initialize_routes(api):
    # add new routes to get / add / delete / update datasets
    api.add_resource(DatasetsController, '/api/datasets')
    api.add_resource(DatasetController, '/api/datasets/<id>')  # id of dataset

    api.add_resource(DatasetImageApi, '/api/datasets/getimage/<id_ds>/<id_img>')  # id of dataset

    api.add_resource(DatasetCreator, '/api/dataset-creator')  # temporary route for materialize dataset
    api.add_resource(SegmentationDatasetCreator, '/api/segmentation-dataset-creator')

    api.add_resource(ModelsApi, '/api/models')
    api.add_resource(ModelApi, '/api/models/<id>')

