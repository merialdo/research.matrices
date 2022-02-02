import json
import os
import sys
from flask import Response, request, send_file
from flask_restful import Resource
sys.path.append(os.path.realpath(
    os.path.join(os.path.abspath(__file__), os.path.pardir, os.path.pardir, os.path.pardir)))
from backend.library_service.service import DatasetService, PageService, ModelService


# class to handle GET and POST requests for the collection of all the known datasets
class DatasetsController(Resource):

    def __init__(self):
        self.dataset_service = DatasetService()

    # get the collection of all datasets
    def get(self):
        datasets = self.dataset_service.get_all_datasets()
        return Response(datasets, mimetype="application/json", status=200)

    # add a new dataset to the collection
    def post(self):
        # get pages and samples from the request
        all_pages_samples_dict = json.loads(request.form.get('annotations'))
        form_dict = request.form.to_dict()
        form_dict.pop('annotations')
        files = request.files.to_dict().items()

        # the description field is not required, so its default value is None
        if "description" not in form_dict:
            form_dict["description"] = None

        new_dataset = self.dataset_service.create_new_dataset(form=form_dict,
                                                              page_files=files,
                                                              pages_samples_dict=all_pages_samples_dict)
        return {'id': str(new_dataset.id)}, 200


# class to handle GET, PUT, DELETE requests for a single dataset
class DatasetController(Resource):

    def __init__(self):
        self.dataset_service = DatasetService()

    def get(self, id):
        dataset = self.dataset_service.get_dataset_by_id(id)
        return Response(dataset.to_json(), mimetype='application/json', status=200)

    # update a stored dataset
    def put(self, id):
        pages_samples = request.form.get('annotations')
        pages_samples_dict = json.loads(pages_samples)

        dataset = self.dataset_service.replace_samples_in_dataset(dataset_id=id, pages_samples_dict=pages_samples_dict)

        return 'Updated dataset ' + str(dataset.id), 200

    # delete a stored dataset
    def delete(self, id):
        self.dataset_service.delete_dataset_by_id(dataset_id=id)
        return 'Deleted dataset ' + str(id), 200


class DatasetImageController(Resource):
    def __init__(self):
        self.page_service = PageService()

    def get(self, id_ds, id_img):
        page = self.page_service.get_page_content_by_id(page_id=id_img)
        return Response({page}, mimetype='image/png', status=200)


# export dataset!
class DatasetExportController(Resource):

    def __init__(self):
        self.dataset_service = DatasetService()

    def post(self):

        dataset_path = None
        try:
            # get the datase name
            dataset_name = request.form.get('name')
            # get the list of page files
            files = request.files.to_dict().items()
            # get the dictionary of samples
            all_pages_samples_dict = json.loads(request.form.get('annotations'))

            dataset_path = self.dataset_service.save_dataset_locally(dataset_name=dataset_name,
                                                                     dataset_files=files,
                                                                     dataset_samples_dict=all_pages_samples_dict)
            print(dataset_path)
            return send_file(dataset_path,
                             mimetype='application/zip',
                             as_attachment=True,
                             attachment_filename=dataset_name + '.zip')
        finally:
            os.remove(dataset_path)


# class to handle  get and post operations on model collection
class ModelsController(Resource):

    def __init__(self):
        self.model_service = ModelService()

    # get the collection of models
    def get(self):
        models = self.model_service.get_all_models().to_json()
        return Response(models, mimetype="application/json", status=200)

    # add a new model to model collection
    def post(self):
        body = request.get_json()
        name, language, description = body["name"], body["language"], body["description"]
        weights, h_avg = body["weights"], body["h_avg"]
        training_data = body["training_data"]   # todo: handle the training_data
        model = self.model_service.create_new_model(name=name, language=language, description=description,
                                                    weights=weights, h_avg=h_avg, training_data=training_data)
        return {'id': str(model)}, 200


# class to handle get,put,delete operations on a model
class ModelController(Resource):
    def __init__(self):
        self.model_service = ModelService()

    # retrieve model by id
    def get(self, id):
        model = self.model_service.get_model_by_id(model_id=id).to_json()
        return Response(model, mimetype='application/json', status=200)

    # delete model by id
    def delete(self, id):
        self.model_service.delete_model_by_id(model_id=id)
        return 'Deleted model ' + str(id), 200

    # update a stored model
    def put(self, id):
        body = request.get_json()
        self.model_service.update_model_by_id(model_id=id, **body)
        return 'updated model ' + str(id), 200
