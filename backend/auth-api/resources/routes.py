from .model import ModelsApi, ModelApi
from .dataset import DatasetsApi, DatasetApi, DatasetImageApi, DatasetCreator, SegmentationDatasetCreator
from .auth import SignupApi, LoginApi


def initialize_routes(api):
    api.add_resource(ModelsApi, '/api/models')
    api.add_resource(ModelApi, '/api/models/<id>')

    api.add_resource(DatasetsApi, '/api/datasets')
    api.add_resource(DatasetApi, '/api/datasets/<id>')  # id of dataset

    api.add_resource(DatasetImageApi, '/api/datasets/getimage/<id_ds>/<id_img>')  # id of dataset

    api.add_resource(DatasetCreator, '/api/dataset-creator')  # temporary route for materialize dataset
    api.add_resource(SegmentationDatasetCreator, '/api/segmentation-dataset-creator')

    api.add_resource(SignupApi, '/api/auth/signup')
    api.add_resource(LoginApi, '/api/auth/login')
    
