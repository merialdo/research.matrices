import shutil
import cv2
import json
import os
import gridfs
import math
import sys
from bson import ObjectId
from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist, \
    ValidationError, InvalidQueryError

from backend.library_service.config import LIBRARY_ROOT

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

    def _resize_image_bigsize(self, img2resize, big_size):
        height, width, _ = img2resize.shape
        if height > width:
            new_height = big_size
            new_width = new_height / height * width
        else:
            new_width = big_size
            new_height = new_width / width * height
        new_height = int(round(new_height / 32) * 32)
        new_width = int(round(new_width / 32) * 32)
        resized_img = cv2.resize(img2resize, (new_width, new_height))
        return resized_img, new_width, new_height

    def save_dataset_locally(self,
                             dataset_name: str,
                             dataset_files,
                             dataset_samples_dict):

        temporary_dataset_root = os.path.join(LIBRARY_ROOT, dataset_name)
        if not os.path.isdir(temporary_dataset_root):
            os.mkdir(temporary_dataset_root)

        dbnet_dataset = dict()  # DBNET
        dbnet_dataset['data_root'] = 'raw_images'  # DBNET
        dbnet_dataset['data_list'] = []  # DBNET
        dbnet_dataset_root = os.path.join(temporary_dataset_root, dbnet_dataset['data_root'])  # DBNET

        if not os.path.isdir(os.path.join(temporary_dataset_root, dbnet_dataset['data_root'])):  # DBNET
            os.mkdir(dbnet_dataset_root)

        gt_name = 'dataset.json'

        for index_file, (k, v) in enumerate(dataset_files):
            # filename_gt = k.split('.')[0] + '.json'
            filename_img = k
            boxes = dataset_samples_dict[k]['boxes']
            v.save(os.path.join(dataset_name, 'raw_images', filename_img))  # save  full img

            ocr_folder_path = os.path.join(dataset_name, 'clips', k)
            if not os.path.isdir(ocr_folder_path):
                os.makedirs(ocr_folder_path)

            img = cv2.imread(os.path.join(dataset_name, 'raw_images', filename_img))
            height, width, _ = img.shape
            img_resized, resized_w, resized_h = self._resize_image_bigsize(img, big_size=2500)
            cv2.imwrite(os.path.join(dataset_name, 'raw_images', filename_img), img_resized,
                        [cv2.IMWRITE_JPEG_QUALITY, 100])
            aspect_ratio_w = resized_w / width
            aspect_ratio_h = resized_h / height

            dbnet_dataset_elem = dict()  # DBNET
            dbnet_dataset_elem['img_name'] = filename_img  # DBNET
            dbnet_dataset_elem['annotations'] = []  # DBNET

            for index_box, box in enumerate(boxes):
                x1, y1, w, h = box['x'], box['y'], box['width'], box['height']
                x2, y2 = x1 + w, y1
                x3, y3 = x1 + w, y1 + h
                x4, y4 = x1, y1 + h
                polygon = [[x1 * aspect_ratio_w, y1 * aspect_ratio_h], [x2 * aspect_ratio_w, y2 * aspect_ratio_h],
                           [x3 * aspect_ratio_w, y3 * aspect_ratio_h], [x4 * aspect_ratio_w, y4 * aspect_ratio_h]]

                dbnet_annotation = dict()  # DBNET
                dbnet_annotation['illegibility'] = False
                dbnet_annotation['language'] = "Latin"
                dbnet_annotation['chars'] = [{
                    'polygon': [],
                    'char': "",
                    'illegibility': False,
                    'language': "Latin"
                }]

                dbnet_annotation['polygon'] = polygon
                dbnet_annotation['text'] = box['text']

                dbnet_dataset_elem['annotations'].append(dbnet_annotation)

                x = math.ceil(box['x'])
                y = math.ceil(box['y'])
                w = math.ceil(box['width'])
                h = math.ceil(box['height'])
                text = box['text']

                crop_img = img[y:y + h, x:x + w]
                file_name = str(index_file) + '_' + str(index_box)

                cv2.imwrite(ocr_folder_path + '/' + dataset_name + '_' + file_name + '.jpg', crop_img,
                            [cv2.IMWRITE_JPEG_QUALITY, 100])
                with open(ocr_folder_path + '/' + dataset_name + '_' + file_name + '.jpg.txt', "w",
                          encoding='utf-8') as gt:  # need text encoding?
                    gt.write(text)

            dbnet_dataset['data_list'].append(dbnet_dataset_elem)  # DBNET

        with open(dataset_name + '/' + gt_name, 'w') as gt_json:
            json.dump(dbnet_dataset, gt_json)

        shutil.copyfile(os.path.join(LIBRARY_ROOT, 'scripts', 'generate_dbnet_dataset.py'),
                        os.path.join(temporary_dataset_root, 'generate_dbnet_dataset.py'))
        shutil.copyfile(os.path.join(LIBRARY_ROOT, 'scripts', 'generate_ocr_dataset.py'),
                        os.path.join(temporary_dataset_root, 'generate_ocr_dataset.py'))
        shutil.copyfile(os.path.join(LIBRARY_ROOT, 'scripts', 'split.json'),
                        os.path.join(temporary_dataset_root, 'split.json'))

        shutil.make_archive(temporary_dataset_root, "zip", temporary_dataset_root)
        shutil.rmtree(temporary_dataset_root)

        return temporary_dataset_root + ".zip"

    def save_dataset_locally_2(self,
                             dataset_name: str,
                             dataset_files,
                             dataset_samples_dict):
        try:
            temporary_dataset_root = os.path.join(LIBRARY_ROOT, dataset_name)
            if not os.path.isdir(temporary_dataset_root):
                os.mkdir(temporary_dataset_root)

            dbnet_dataset = dict()  # DBNET
            dbnet_dataset['data_root'] = 'raw_images'  # DBNET
            dbnet_dataset['data_list'] = []  # DBNET
            dbnet_dataset_root = os.path.join(temporary_dataset_root, dbnet_dataset['data_root'])  # DBNET

            if not os.path.isdir(os.path.join(temporary_dataset_root, dbnet_dataset['data_root'])):  # DBNET
                os.mkdir(dbnet_dataset_root)

            gt_name = 'dataset.json'

            for index_file, (k, v) in enumerate(dataset_files):
                # filename_gt = k.split('.')[0] + '.json'
                filename_img = k
                boxes = dataset_samples_dict[k]['boxes']
                v.save(os.path.join(dataset_name, 'raw_images', filename_img))  # save  full img

                ocr_folder_path = os.path.join(dataset_name, 'clips', k)
                if not os.path.isdir(ocr_folder_path):
                    os.makedirs(ocr_folder_path)

                img = cv2.imread(os.path.join(dataset_name, 'raw_images', filename_img))
                height, width, _ = img.shape
                img_resized, resized_w, resized_h = self._resize_image_bigsize(img, big_size=2500)
                cv2.imwrite(os.path.join(dataset_name, 'raw_images', filename_img), img_resized,
                            [cv2.IMWRITE_JPEG_QUALITY, 100])
                aspect_ratio_w = resized_w / width
                aspect_ratio_h = resized_h / height

                dbnet_dataset_elem = dict()  # DBNET
                dbnet_dataset_elem['img_name'] = filename_img  # DBNET
                dbnet_dataset_elem['annotations'] = []  # DBNET

                for index_box, box in enumerate(boxes):
                    x1, y1, w, h = box['x'], box['y'], box['width'], box['height']
                    x2, y2 = x1 + w, y1
                    x3, y3 = x1 + w, y1 + h
                    x4, y4 = x1, y1 + h
                    polygon = [[x1 * aspect_ratio_w, y1 * aspect_ratio_h], [x2 * aspect_ratio_w, y2 * aspect_ratio_h],
                               [x3 * aspect_ratio_w, y3 * aspect_ratio_h], [x4 * aspect_ratio_w, y4 * aspect_ratio_h]]

                    dbnet_annotation = dict()  # DBNET
                    dbnet_annotation['illegibility'] = False
                    dbnet_annotation['language'] = "Latin"
                    dbnet_annotation['chars'] = [{
                        'polygon': [],
                        'char': "",
                        'illegibility': False,
                        'language': "Latin"
                    }]

                    dbnet_annotation['polygon'] = polygon
                    dbnet_annotation['text'] = box['text']

                    dbnet_dataset_elem['annotations'].append(dbnet_annotation)

                    x = math.ceil(box['x'])
                    y = math.ceil(box['y'])
                    w = math.ceil(box['width'])
                    h = math.ceil(box['height'])
                    text = box['text']

                    crop_img = img[y:y + h, x:x + w]
                    file_name = str(index_file) + '_' + str(index_box)

                    cv2.imwrite(ocr_folder_path + '/' + dataset_name + '_' + file_name + '.jpg', crop_img,
                                [cv2.IMWRITE_JPEG_QUALITY, 100])
                    with open(ocr_folder_path + '/' + dataset_name + '_' + file_name + '.jpg.txt', "w",
                              encoding='utf-8') as gt:  # need text encoding?
                        gt.write(text)

                dbnet_dataset['data_list'].append(dbnet_dataset_elem)  # DBNET

            with open(dataset_name + '/' + gt_name, 'w') as gt_json:
                json.dump(dbnet_dataset, gt_json)

            shutil.copyfile(os.path.join(LIBRARY_ROOT, 'scripts', 'generate_dbnet_dataset.py'),
                            os.path.join(temporary_dataset_root, 'generate_dbnet_dataset.py'))
            shutil.copyfile(os.path.join(LIBRARY_ROOT, 'scripts', 'generate_ocr_dataset.py'),
                            os.path.join(temporary_dataset_root, 'generate_ocr_dataset.py'))
            shutil.copyfile(os.path.join(LIBRARY_ROOT, 'scripts', 'split.json'),
                            os.path.join(temporary_dataset_root, 'split.json'))

            shutil.make_archive(temporary_dataset_root, "zip", temporary_dataset_root)
            shutil.rmtree(temporary_dataset_root)

            return temporary_dataset_root + ".zip"

        except Exception as e:
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


class ModelService:

    def get_all_models(self):
        try:
            return Model.objects
        except DoesNotExist:
            raise ObjectDoesNotExistException
        except Exception:
            raise InternalServerException

    def get_model_by_id(self, model_id):
        try:
            return Model.objects.get(id=model_id)
        except DoesNotExist:
            raise DeletingModelException
        except Exception:
            raise InternalServerException

    def create_new_model(self, name, language, description, weights, h_avg, training_data):
        try:
            #todo: handle the training_data, that are must be a reference to a pre-existing dataset
            model = Model.from_fields(name, language, description, weights, h_avg, training_data)
            model.save()
            return model
        except (FieldDoesNotExist, ValidationError):
            raise SchemaValidationException
        except NotUniqueError:
            raise ObjectAlreadyExistsException
        except Exception as e:
            raise InternalServerException

    def update_model_by_id(self, model_id, **body):
        try:
            Model.objects.get(id=model_id).update(**body)
            return True
        except InvalidQueryError:
            raise SchemaValidationException
        except DoesNotExist:
            raise UpdatingModelException
        except Exception:
            raise InternalServerException

    def delete_model_by_id(self, model_id):
        try:
            model = Model.objects.get(id=model_id)
            model.delete()
            return True
        except DoesNotExist:
            raise DeletingModelException
        except Exception:
            raise InternalServerException
