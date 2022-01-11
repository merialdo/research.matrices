import shutil
import cv2
import json
import os
import gridfs
import math
import sys
from pymongo import MongoClient
from bson import ObjectId
from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist, \
    ValidationError, InvalidQueryError

sys.path.append(os.path.realpath(
    os.path.join(os.path.abspath(__file__), os.path.pardir, os.path.pardir, os.path.pardir)))

from backend.library_service.domain_model import Dataset, Page, Sample, Model
from backend.library_service.database import db

from backend.library_service.errors import \
    SchemaValidationException, \
    ObjectAlreadyExistsException, \
    InternalServerException, \
    UpdatingModelException, \
    DeletingModelException, \
    ObjectDoesNotExistException


class DatasetService:
    """The DatasetService performs operations on the datasets"""

    def get_all_datasets(self):
        try:
            return Dataset.objects
        except DoesNotExist:
            raise ObjectDoesNotExistException
        except Exception:
            raise InternalServerException

    def create_new_dataset(self, form, page_files, pages_samples_dict):
        try:
            new_dataset_pages = []
            for filename, content in page_files:

                cur_page_samples = pages_samples_dict[filename]
                new_page = Page.from_fields(filename=filename,
                                            content=content,
                                            is_confirmed=cur_page_samples['is_confirmed'],
                                            list_active_texts=[str(x) for x in cur_page_samples['list_active_texts']],
                                            index=cur_page_samples['index'])
                new_dataset_pages.append(new_page)

                if filename in pages_samples_dict.keys():  # check if annotation is partial in current dataset
                    samples_dict = cur_page_samples['boxes']
                    for cur_sample_dict in samples_dict:
                        new_sample = Sample.from_fields(x=cur_sample_dict['x'],
                                                        y=cur_sample_dict['y'],
                                                        width=cur_sample_dict['width'],
                                                        height=cur_sample_dict['height'],
                                                        text=cur_sample_dict['text'])
                        new_page.samples.append(new_sample)

            new_dataset = Dataset.from_fields(name=form["name"],
                                              language=form["language"],
                                              description=form["description"],
                                              pages=new_dataset_pages)
            new_dataset.save()
            return new_dataset

        except (FieldDoesNotExist, ValidationError):
            raise SchemaValidationException
        except NotUniqueError:
            raise ObjectAlreadyExistsException
        except Exception as e:
            raise InternalServerException

    def get_dataset_by_id(self, dataset_id):
        try:
            return Dataset.objects.get(id=dataset_id)
        except DoesNotExist:
            raise DeletingModelException
        except Exception:
            raise InternalServerException

    # update a stored dataset
    def replace_samples_in_dataset(self, dataset_id, pages_samples_dict):
        try:
            dataset = Dataset.objects.get(id=dataset_id)

            for i, filename in enumerate(pages_samples_dict.keys()):
                cur_page_new_samples = []
                for cur_sample_dict in pages_samples_dict[filename]['boxes']:
                    new_sample = Sample.from_fields(x=cur_sample_dict['x'],
                                                    y=cur_sample_dict['y'],
                                                    width=cur_sample_dict['width'],
                                                    height=cur_sample_dict['height'],
                                                    text=cur_sample_dict['text'])
                    cur_page_new_samples.append(new_sample)

                dataset.pages[i].samples = cur_page_new_samples
            dataset.save()
            return dataset
        except InvalidQueryError:
            raise SchemaValidationException
        except DoesNotExist:
            raise UpdatingModelException
        except Exception:
            raise InternalServerException

    # delete a stored dataset
    def delete_dataset_by_id(self, dataset_id):
        try:
            dataset = Dataset.objects.get(id=dataset_id)
            dataset.delete()
            return True
        except DoesNotExist:
            raise DeletingModelException
        except Exception:
            raise InternalServerException


class PageService:

    def get_page_content_by_id(self, page_id):
        try:
            fs = gridfs.GridFS(db, collection='fs')
            page = fs.get(file_id=ObjectId(page_id)).read()
            return page

        except DoesNotExist:
            raise ObjectDoesNotExistException
        except Exception:
            raise InternalServerException

