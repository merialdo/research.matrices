"""Dataset reader and process"""

import os
import html
import string
import random
import multiprocessing
import xml.etree.ElementTree as ET
from glob import glob
from tqdm import tqdm
import preproc as pp
from functools import partial
from pathlib import Path
import numpy as np
import h5py
from itertools import groupby
import unicodedata
import re


def remove_annotations(gt_text):
    gt_text = re.sub("\{.*?\}", "", gt_text)
    gt_text = gt_text.replace('(','').replace(')','')
    return gt_text.strip()


class Tokenizer() :
    """Manager tokens functions and charset/dictionary properties"""

    def __init__(self , chars , max_text_length=128) :
        self.PAD_TK , self.UNK_TK = "¶" , "¤"
        self.chars = (self.PAD_TK + self.UNK_TK + chars)

        self.PAD = self.chars.find(self.PAD_TK)
        self.UNK = self.chars.find(self.UNK_TK)

        self.vocab_size = len(self.chars)
        self.maxlen = max_text_length


    def encode(self , text) :
        """Encode text to vector"""

        if isinstance(text , bytes) :
            text = text.decode()

        text = unicodedata.normalize("NFKD" , text).encode("ASCII" , "ignore").decode("ASCII")
        # if (self.check_carplates(text)):
        #    text = text[:2] + " " + text[2:]
        text = " ".join(text.split())

        groups = ["".join(group) for _ , group in groupby(text)]
        text = "".join([self.UNK_TK.join(list(x)) if len(x) > 1 else x for x in groups])
        encoded = []

        for item in text :
            index = self.chars.find(item)

            index = self.UNK if index == -1 else index
            encoded.append(index)

        return np.asarray(encoded)

    def decode(self , text) :
        """Decode vector to text"""

        decoded = "".join([self.chars[int(x)] for x in text if x > -1])
        decoded = self.remove_tokens(decoded)

        return decoded

    def remove_tokens(self , text) :
        """Remove tokens (PAD) from text"""

        return text.replace(self.PAD_TK , "").replace(self.UNK_TK , "")


class Dataset():
    """Dataset class to read images and sentences from base (raw files)"""

    def __init__(self, source, name):
        self.source = source
        self.name = name
        self.dataset = None
        self.partitions = ['train', 'valid', 'test']

    def read_partitions(self):
        """Read images and sentences from dataset"""

        dataset = getattr(self, f"_{self.name}")()

        if not self.dataset:
            self.dataset = self._init_dataset()

        for y in self.partitions:
            self.dataset[y]['dt'] += dataset[y]['dt']
            self.dataset[y]['gt'] += dataset[y]['gt']

    def save_partitions(self, target, image_input_size, max_text_length):
        """Save images and sentences from dataset"""

        os.makedirs(os.path.dirname(target), exist_ok=True)
        total = 0
        print("Create Hdf5")

        with h5py.File(target, "w") as hf:
            for pt in self.partitions:
                self.dataset[pt] = self.check_text(self.dataset[pt], max_text_length)

                size = (len(self.dataset[pt]['dt']),) + image_input_size[:2]
                total += size[0]

                dummy_image = np.zeros(size, dtype=np.uint8)
                dummy_sentence = [("c" * max_text_length).encode()] * size[0]

                hf.create_dataset(f"{pt}/dt", data=dummy_image, compression="gzip", compression_opts=9)
                hf.create_dataset(f"{pt}/gt", data=dummy_sentence, compression="gzip", compression_opts=9)

        pbar = tqdm(total=total)
        batch_size = 60 * 10

        print("Start")
        all_imgs = []
        all_gts = []

        for pt in self.partitions:

            for batch in range(0, len(self.dataset[pt]['gt']), batch_size):
                images = []

                if (True):
                    with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
                        r = pool.map(partial(pp.preprocess, input_size=image_input_size),
                                     self.dataset[pt]['dt'][batch:batch + batch_size])
                        images.append(r)
                        pool.close()
                        pool.join()

                    with h5py.File(target, "a") as hf:
                        print(images)
                        hf[f"{pt}/dt"][batch:batch + batch_size] = images
                        hf[f"{pt}/gt"][batch:batch + batch_size] = [s.encode() for s in
                                                                    self.dataset[pt]['gt'][batch:batch + batch_size]]
                        pbar.update(batch_size)
                # except:
                #    print(self.dataset[pt]['dt'][batch :batch + batch_size])
                #    print("An error occurred ")
                '''
        json_train = {}
        json_test = {}
        if(not os.path.isdir("dataset")):
            os.makedirs("dataset/val")
            os.makedirs("dataset/train")
        for pt in self.partitions :
            if(pt != "valid"):
                for i,elem in tqdm(enumerate(self.dataset[pt]['gt'])):
                    gt = elem
                    img = self.dataset[pt]['dt'][i]
                    #print(img)
                    gt = unicodedata.normalize("NFKD", gt).encode("ASCII", "ignore").decode("ASCII")
                    gt = " ".join(gt.split())

                    if(len(gt) > 0  and len(gt) < 180):

                        if isinstance(img , str) :
                            name = img.split("/")[-1]

                        if isinstance(img , tuple) :
                            name = img[0].split("/")[-1]

                        no_format = name.split(".")[0]
                        if(1>0):
                            try:
                                img = pp.preprocess2(img)
                                app_img = img
                                x = aug(app_img.astype(np.uint8))
                                #print(x.shape)
                                if(pt == "train"):
                                    cv2.imwrite("dataset/train/"+no_format+".jpg",img)
                                    json_train[no_format+".jpg"]  = gt
                                elif(pt == "test"):
                                    cv2.imwrite("dataset/val/" + no_format + ".jpg" , img)
                                    json_test[no_format + ".jpg"] = gt
                                else:
                                    continue
                            except Exception as ex:
                                print(img)
                                print('type is:' , ex.__class__.__name__)
                                continue




        with open(os.path.join("dataset" , "train_labels.json") , 'w') as fp :
            json.dump(json_train , fp)
        with open(os.path.join("dataset" , "val_labels.json") , 'w') as fp :
            json.dump(json_test , fp)

         '''

    def save_partitions(self, target, image_input_size, max_text_length):
        """Save images and sentences from dataset"""

        os.makedirs(os.path.dirname(target), exist_ok=True)
        total = 0

        with h5py.File(target, "w") as hf:
            for pt in self.partitions:
                self.dataset[pt] = self.check_text(self.dataset[pt], max_text_length)
                size = (len(self.dataset[pt]['dt']),) + image_input_size[:2]
                total += size[0]

                dummy_image = np.zeros(size, dtype=np.uint8)
                dummy_sentence = [("c" * max_text_length).encode()] * size[0]
                print("Size", size)
                hf.create_dataset(f"{pt}/dt", data=dummy_image, compression="gzip", compression_opts=9)
                hf.create_dataset(f"{pt}/gt", data=dummy_sentence, compression="gzip", compression_opts=9)

        pbar = tqdm(total=total)
        batch_size = 60

        for pt in self.partitions:
            for batch in range(0, len(self.dataset[pt]['gt']), batch_size):
                images = []

                with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
                    r = pool.map(partial(pp.preprocess, input_size=image_input_size),
                                 self.dataset[pt]['dt'][batch:batch + batch_size])
                    images.append(r)
                    pool.close()
                    pool.join()
                # print(images)

                with h5py.File(target, "a") as hf:
                    hf[f"{pt}/dt"][batch:batch + batch_size] = images
                    hf[f"{pt}/gt"][batch:batch + batch_size] = [s.encode() for s in self.dataset[pt]
                                                                                    ['gt'][batch:batch + batch_size]]
                    pbar.update(batch_size)

    def _init_dataset(self):
        dataset = dict()

        for i in self.partitions:
            dataset[i] = {"dt": [], "gt": []}

        return dataset

    def _shuffle(self, *ls):
        random.seed(42)

        if len(ls) == 1:
            li = list(*ls)
            random.shuffle(li)
            return li

        li = list(zip(*ls))
        random.shuffle(li)
        return zip(*li)

    def _hdsr14_car_a(self):
        """ICFHR 2014 Competition on Handwritten Digit String Recognition in Challenging Datasets dataset reader"""

        dataset = self._init_dataset()
        partition = self._read_orand_partitions(os.path.join(self.source, "ORAND-CAR-2014"), 'a')

        for pt in self.partitions:
            for item in partition[pt]:
                text = " ".join(list(item[1]))
                dataset[pt]['dt'].append(item[0])
                dataset[pt]['gt'].append(text)

        return dataset

    def _hdsr14_car_b(self):
        """ICFHR 2014 Competition on Handwritten Digit String Recognition in Challenging Datasets dataset reader"""

        dataset = self._init_dataset()
        partition = self._read_orand_partitions(os.path.join(self.source, "ORAND-CAR-2014"), 'b')

        for pt in self.partitions:
            for item in partition[pt]:
                text = " ".join(list(item[1]))
                dataset[pt]['dt'].append(item[0])
                dataset[pt]['gt'].append(text)

        return dataset

    def _read_orand_partitions(self, basedir, type_f):
        """ICFHR 2014 Competition on Handwritten Digit String Recognition in Challenging Datasets dataset reader"""

        partition = {"train": [], "valid": [], "test": []}
        folder = f"CAR-{type_f.upper()}"

        for i in ['train', 'test']:
            img_path = os.path.join(basedir, folder, f"{type_f.lower()}_{i}_images")
            txt_file = os.path.join(basedir, folder, f"{type_f.lower()}_{i}_gt.txt")

            with open(txt_file) as f:
                lines = [line.replace("\n", "").split("\t") for line in f]
                lines = [[os.path.join(img_path, x[0]), x[1]] for x in lines]

            partition[i] = lines

        sub_partition = int(len(partition['train']) * 0.1)
        partition['valid'] = partition['train'][:sub_partition]
        partition['train'] = partition['train'][sub_partition:]

        return partition

    def _hdsr14_cvl(self):
        """ICFHR 2014 Competition on Handwritten Digit String Recognition in Challenging Datasets dataset reader"""

        dataset = self._init_dataset()
        partition = {"train": [], "valid": [], "test": []}

        glob_filter = os.path.join(self.source, "cvl-strings", "**", "*.png")
        train_list = [x for x in glob(glob_filter, recursive=True)]

        glob_filter = os.path.join(self.source, "cvl-strings-eval", "**", "*.png")
        test_list = [x for x in glob(glob_filter, recursive=True)]

        sub_partition = int(len(train_list) * 0.1)
        partition['valid'].extend(train_list[:sub_partition])
        partition['train'].extend(train_list[sub_partition:])
        partition['test'].extend(test_list[:])

        for pt in self.partitions:
            for item in partition[pt]:
                text = " ".join(list(os.path.basename(item).split("-")[0]))
                dataset[pt]['dt'].append(item)
                dataset[pt]['gt'].append(text)

        return dataset

    def _bentham(self):
        """Bentham dataset reader"""

        source = os.path.join(self.source, "BenthamDatasetR0-GT")
        pt_path = os.path.join(source, "Partitions")

        paths = {"train": open(os.path.join(pt_path, "TrainLines.lst")).read().splitlines(),
                 "valid": open(os.path.join(pt_path, "ValidationLines.lst")).read().splitlines(),
                 "test": open(os.path.join(pt_path, "TestLines.lst")).read().splitlines()}

        transcriptions = os.path.join(source, "Transcriptions")
        gt = os.listdir(transcriptions)
        gt_dict = dict()

        for index, x in enumerate(gt):
            text = " ".join(open(os.path.join(transcriptions, x)).read().splitlines())
            text = html.unescape(text).replace("<gap/>", "")
            gt_dict[os.path.splitext(x)[0]] = " ".join(text.split())

        img_path = os.path.join(source, "Images", "Lines")
        dataset = self._init_dataset()

        for i in self.partitions:
            for line in paths[i]:
                dataset[i]['dt'].append(os.path.join(img_path, f"{line}.png"))
                dataset[i]['gt'].append(gt_dict[line])

        return dataset

    def _iam(self):
        """IAM dataset reader"""

        pt_path = os.path.join(self.source, "largeWriterIndependentTextLineRecognitionTask")
        valid2 = open(os.path.join(pt_path, "validationset2.txt")).read().splitlines()
        paths = {"train": open(os.path.join(pt_path, "trainset.txt")).read().splitlines() + valid2[0:322],
                 "valid": open(os.path.join(pt_path, "validationset1.txt")).read().splitlines() + valid2[322:398],
                 "test": open(os.path.join(pt_path, "testset.txt")).read().splitlines() + valid2[398:]}

        lines = open(os.path.join(self.source, "ascii", "lines.txt")).read().splitlines()
        dataset = self._init_dataset()
        gt_dict = dict()

        for line in lines:
            if (not line or line[0] == "#"):
                continue

            split = line.split()

            if split[1] == "ok":
                gt_dict[split[0]] = " ".join(split[8::]).replace("|", " ")

        for i in self.partitions:
            for line in paths[i]:
                try:
                    split = line.split("-")
                    folder = f"{split[0]}-{split[1]}"

                    img_file = f"{split[0]}-{split[1]}-{split[2]}.png"
                    img_path = os.path.join(self.source, "lines", split[0], folder, img_file)

                    dataset[i]['gt'].append(gt_dict[line])
                    dataset[i]['dt'].append(img_path)
                except KeyError:
                    pass

        return dataset

    def _biagini(self):
        """Biagini Camera Deputati dataset reader"""

        paths = sorted(glob(os.path.join(self.source, "*.jpg")))
        gt = sorted(glob(os.path.join(self.source, "*.txt")))

        dataset = self._init_dataset()
        train = [(line, gt[i]) for i, line in enumerate(paths)]
        test = [(line, gt[i]) for i, line in enumerate(paths) if i % 5 == 0 and not i % 9 == 0]
        valid = [(line, gt[i]) for i, line in enumerate(paths) if i % 9 == 0 and not i % 5 == 0]
        train = [item for item in train if item not in valid]
        train = [item for item in train if item not in test]
        paths = {"train": train,
                 "valid": valid,
                 "test": test}

        for i in self.partitions:
            for line in paths[i]:
                with open(line[1], 'r', encoding='latin-1')as gt:
                    # print(gt.read().splitlines()[0])
                    dataset[i]['gt'].append(gt.read().splitlines()[0])
                    dataset[i]['dt'].append(line[0])

        return dataset

    def _rimes(self):
        """Rimes dataset reader"""

        def generate(xml, subpath, paths, validation=False):
            xml = ET.parse(os.path.join(self.source, xml)).getroot()
            dt = []

            for page_tag in xml:
                page_path = page_tag.attrib['FileName']

                for i, line_tag in enumerate(page_tag.iter("Line")):
                    text = html.unescape(line_tag.attrib['Value'])
                    text = " ".join(text.split())

                    bound = [abs(int(line_tag.attrib['Top'])), abs(int(line_tag.attrib['Bottom'])),
                             abs(int(line_tag.attrib['Left'])), abs(int(line_tag.attrib['Right']))]
                    dt.append([os.path.join(subpath, page_path), text, bound])

            if validation:
                index = int(len(dt) * 0.9)
                paths['valid'] = dt[index:]
                paths['train'] = dt[:index]
            else:
                paths['test'] = dt

        dataset = self._init_dataset()
        paths = dict()

        generate("training_2011.xml", "training_2011", paths, validation=True)
        generate("eval_2011_annotated.xml", "eval_2011", paths, validation=False)

        for i in self.partitions:
            for item in paths[i]:
                boundbox = [item[2][0], item[2][1], item[2][2], item[2][3]]
                img_p = item[0].replace("images/", "")
                dataset[i]['dt'].append((os.path.join(self.source, img_p), boundbox))
                dataset[i]['gt'].append(item[1])

        return dataset

    def _saintgall(self):
        """Saint Gall dataset reader"""

        pt_path = os.path.join(self.source, "sets")

        paths = {"train": open(os.path.join(pt_path, "train.txt")).read().splitlines(),
                 "valid": open(os.path.join(pt_path, "valid.txt")).read().splitlines(),
                 "test": open(os.path.join(pt_path, "test.txt")).read().splitlines()}

        lines = open(os.path.join(self.source, "ground_truth", "transcription.txt")).read().splitlines()
        gt_dict = dict()

        for line in lines:
            split = line.split()
            split[1] = split[1].replace("-", "").replace("|", " ")
            gt_dict[split[0]] = split[1]

        img_path = os.path.join(self.source, "data", "line_images_normalized")
        dataset = self._init_dataset()

        for i in self.partitions:
            for line in paths[i]:
                glob_filter = os.path.join(img_path, f"{line}*")
                img_list = [x for x in glob(glob_filter, recursive=True)]

                for line in img_list:
                    line = os.path.splitext(os.path.basename(line))[0]
                    dataset[i]['dt'].append(os.path.join(img_path, f"{line}.png"))
                    dataset[i]['gt'].append(gt_dict[line])

        return dataset

    def _washington(self):
        """Washington dataset reader"""

        pt_path = os.path.join(self.source, "sets", "cv1")

        paths = {"train": open(os.path.join(pt_path, "train.txt")).read().splitlines(),
                 "valid": open(os.path.join(pt_path, "valid.txt")).read().splitlines(),
                 "test": open(os.path.join(pt_path, "test.txt")).read().splitlines()}

        lines = open(os.path.join(self.source, "ground_truth", "transcription.txt")).read().splitlines()
        gt_dict = dict()

        for line in lines:
            split = line.split()
            split[1] = split[1].replace("-", "").replace("|", " ")
            split[1] = split[1].replace("s_pt", ".").replace("s_cm", ",")
            split[1] = split[1].replace("s_mi", "-").replace("s_qo", ":")
            split[1] = split[1].replace("s_sq", ";").replace("s_et", "V")
            split[1] = split[1].replace("s_bl", "(").replace("s_br", ")")
            split[1] = split[1].replace("s_qt", "'").replace("s_GW", "G.W.")
            split[1] = split[1].replace("s_", "")
            gt_dict[split[0]] = split[1]

        img_path = os.path.join(self.source, "data", "line_images_normalized")
        dataset = self._init_dataset()

        for i in self.partitions:
            for line in paths[i]:
                gt = gt_dict[line]
                if (len(gt) > 0):
                    dataset[i]['dt'].append(os.path.join(img_path, f"{line}.png"))
                    dataset[i]['gt'].append(gt)

        return dataset

    def _deutch(self):

        # paths =  sorted(glob(os.path.join(self.source, "**","/*.jpg")))
        paths = sorted(Path(self.source).rglob("*.jpg"))
        gt = sorted(Path(self.source).rglob("*.txt"))

        dataset = self._init_dataset()
        train = [(str(line), str(gt[i])) for i, line in enumerate(paths)]
        test = [(str(line), str(gt[i])) for i, line in enumerate(paths) if i % 5 == 0 and not i % 9 == 0]
        valid = [(str(line), str(gt[i])) for i, line in enumerate(paths) if i % 9 == 0 and not i % 5 == 0]
        train = [item for item in train if item not in valid]
        train = [item for item in train if item not in test]
        paths = {"train": train,
                 "valid": valid,
                 "test": test}

        for i in self.partitions:
            for line in paths[i]:
                with open(line[1], 'r', encoding='latin-1')as gt:
                    g = gt.read().splitlines()[0].strip()
                    if (len(g) > 0):
                        dataset[i]['gt'].append(g)
                        dataset[i]['dt'].append(line[0])

        return dataset

    def _verbali(self):
        """Verbali Camera Deputati dataset reader"""

        paths = sorted(glob(os.path.join(self.source, "*.jpg")))
        gt = sorted(glob(os.path.join(self.source, "*.txt")))

        # print(paths[0],gt[0])
        dataset = self._init_dataset()
        train = [(line, gt[i]) for i, line in enumerate(paths)]
        test = [(line, gt[i]) for i, line in enumerate(paths) if i % 10 == 0]
        valid = test
        train = [item for item in train if item not in valid]
        train = [item for item in train if item not in test]
        paths = {"train": train,
                 "valid": valid,
                 "test": test}

        for i in self.partitions:
            for line in paths[i]:
                with open(line[1], 'r', encoding='latin-1')as gt:
                    g = gt.read().splitlines()[0].strip()
                    if (len(g) > 0):
                        dataset[i]['gt'].append(g)
                        dataset[i]['dt'].append(line[0])
        return dataset

    def _coco(self):
        """Verbali Camera Deputati dataset reader"""

        paths = sorted(glob(os.path.join(self.source, "*.jpg")))
        gt = sorted(glob(os.path.join(self.source, "*.txt")))

        # print(paths[0],gt[0])
        dataset = self._init_dataset()
        train, valid, test = [], [], []
        for i, (line, gt) in enumerate(zip(paths, gt)):
            if (i % 5 == 0):
                test.append((line, gt))
            else:
                train.append((line, gt))

        valid = test
        # train = train[:len(train) ]
        paths = {"train": train,
                 "valid": valid,
                 "test": test}

        for i in self.partitions:
            for line in paths[i]:
                with open(line[1], 'r', encoding='latin-1')as gt:
                    g = gt.read().splitlines()[0].strip()
                    if (len(g) > 0):
                        dataset[i]['gt'].append(g)
                        dataset[i]['dt'].append(line[0])
        return dataset

    def check_test(self, s, test_list):
        for s_test in test_list:
            if (s_test in s):
                return True
        return False

    def check_disp(self, s):

        if ("displacement" in s):
            return False
        else:
            return True

    def _ocr_targhe(self):
        """Verbali Camera Deputati dataset reader"""

        paths = sorted(glob(os.path.join(self.source, "*.jpg")))
        gt = sorted(glob(os.path.join(self.source, "*.txt")))

        test_list = []
        with open("test_list.txt", "r") as test_file:
            for elem in test_file.readlines():
                test_list.append(elem.strip().split(".jpg")[0])

        # print(paths[0],gt[0])
        dataset = self._init_dataset()
        all_data = [(line, gt[i]) for i, line in enumerate(paths)]
        test = []
        train = []
        for line, gt in all_data:
            name = line.split("/")[-1].split(".jpg")[0]
            # print(self.check_test(name , test_list) , self.check_disp(name))
            if (self.check_test(name, test_list) and self.check_disp(name)):
                test.append((line, gt))
                # print(line)
            elif (self.check_test(name, test_list) and not self.check_disp(name)):
                continue
            else:

                train.append((line, gt))

        valid = test
        paths = {"train": train,
                 "valid": valid,
                 "test": test}

        for i in self.partitions:
            for line in paths[i]:
                print(line)
                with open(line[1], 'r', encoding='latin-1')as gt:
                    g = gt.read().splitlines()[0].strip()
                    if (len(g) > 0):
                        # print(gt.read().splitlines()[0])
                        dataset[i]['gt'].append(g)
                        dataset[i]['dt'].append(line[0])
        return dataset

    def _petizioni(self):
        """Petizioni Camera Deputati dataset reader"""

        paths = sorted(glob(os.path.join(self.source, "*.png")))
        gt = sorted(glob(os.path.join(self.source, "*.txt")))

        print(paths[0], gt[0])
        dataset = self._init_dataset()
        train = [(line, gt[i]) for i, line in enumerate(paths)]
        test = [(line, gt[i]) for i, line in enumerate(paths) if i % 95 == 0]
        train = [item for item in train if item not in test]
        valid = test
        paths = {"train": train,
                 "valid": valid,
                 "test": test}

        for i in self.partitions:
            for line in paths[i]:
                with open(line[1], 'r', encoding='latin-1')as gt:
                    # print(gt.read().splitlines()[0])
                    gt = gt.read().splitlines()[0].strip()
                    # print(gt)
                    if (len(gt) > 0):
                        dataset[i]['gt'].append(gt)
                        dataset[i]['dt'].append(line[0])

        return dataset

    def _onorio(self):
        """onorio"""

        paths_train = sorted(Path(self.source + "/train").glob("*.jpg"))
        gt_train = sorted(Path(self.source + "/train").glob("*.txt"))

        paths_test = sorted(Path(self.source + "/test").glob("*.jpg"))
        gt_test = sorted(Path(self.source + "/test").glob("*.txt"))

        dataset = self._init_dataset()
        train = [(str(line), str(gt_train[i])) for i, line in enumerate(paths_train)]
        test = [(str(line), str(gt_test[i])) for i, line in enumerate(paths_test)]
        valid = test

        paths = {"train": train,
                 "valid": valid,
                 "test": test}

        for i in self.partitions:
            for line in paths[i]:
                with open(line[1], 'r', encoding='latin-1')as gt:
                    # print(gt.read().splitlines()[0])
                    gt = gt.read().splitlines()[0].strip()
                    gt = gt.replace("(", "").replace(")", "").replace("'", "")
                    gt = re.sub("\{.*?\}", "", gt)
                    gt = re.sub("\[.*?\]", "", gt)
                    gt = gt.replace("-", "")
                    if (len(gt) > 0):
                        dataset[i]['gt'].append(gt)
                        dataset[i]['dt'].append(line[0])

        return dataset

    @staticmethod
    def check_text(data, max_text_length=180):
        """Checks if the text has more characters instead of punctuation marks"""
        alph = string.digits + string.ascii_letters + string.punctuation + '°' + 'àâéèêëîïôùûçÀÂÉÈËÎÏÔÙÛÇ' + '£€¥¢฿ '
        tokenizer = Tokenizer(alph, max_text_length)

        for i in reversed(range(len(data['gt']))):
            text = pp.text_standardize(data['gt'][i])
            strip_punc = text.strip(string.punctuation).strip()
            no_punc = text.translate(str.maketrans("", "", string.punctuation)).strip()

            length_valid = (len(text) > 0) and (len(text) < max_text_length)
            text_valid = (len(strip_punc) > 1) or (len(no_punc) > 1)

            if (not length_valid) or (not text_valid) or (len(tokenizer.encode(data['gt'][i])) <= 0):
                print("Error", data['gt'][i])
                data['gt'].pop(i)
                data['dt'].pop(i)

        return data

    def clean_text(st):
        alph = string.digits + string.ascii_letters + string.punctuation + '°' + 'àâéèêëîïôùûçÀÂÉÈËÎÏÔÙÛÇ' + '£€¥¢฿ '

        """Checks if the text has more characters instead of punctuation marks"""
        for c in st:
            if (c not in alph):
                return unicodedata.normalize("NFKD", st).encode("ASCII", "ignore").decode("ASCII")

        return st

    def _multilingual(self):
        base_path = self.source

        '''
        self.source = base_path + "rimes"
        rimes = self._rimes()
        self.source = base_path + "bentham"
        print(self.source)
        bentham = self._bentham()
        self.source = base_path + "biagini"
        biagini = self._biagini()
        print(self.source)
        self.source = base_path + "washington"
        washington = self._washington()
        print(self.source)
        self.source = base_path + "iam"
        iam = self._iam()
        print(self.source)
        self.source = base_path + "deutch"
        deutch = self._deutch()
        print(self.source)

        self.source = base_path + "verbali"
        verbali = self._verbali()

        self.source = base_path + "brigantaggio"
        brigantaggio = self._verbali()

        self.source = base_path + "unipol_test"
        unipol = self._petizioni()

        self.source = base_path + "unipol_train"
        unipol_train = self._petizioni()

        self.source = base_path + "sinistri"
        sinistri = self._petizioni()

        self.source = base_path + "date"
        date = self._petizioni()

        #self.source = base_path + "coco"
        #coco = self._coco()

        #self.source = base_path + "carplates_ocr3"
        #targhe = self._ocr_targhe()

        #self.source = base_path + "idcard_ocr"
        #id_card = self._id_card()

        #self.source = base_path + "ocr_color2"
        #ocr = self._ocr()

        #self.source = base_path + "scene_ICDAR"
        #scene_icdar = self._ocr()

        #self.source = base_path + "MLT2019_OCR/train"
        #mlt2019 = self._jpg_only_train()

        #self.source = base_path + "SROIE_OCR"
        #sroie = self._jpg_train_test()
        #self.source = base_path + "SYNTH_120k/train"
        #synth = self._jpg_only_train()
        '''
        self.source = base_path + "onorio"
        dataset = self._onorio()

        '''
        print("Merge")
        dataset = self._init_dataset()

        for i in self.partitions :
            dataset['train']['dt'] += rimes[i]['dt'] + biagini[i]['dt'] + washington[i]['dt'] + sinistri[i]['dt'] + unipol_train[i]['dt']+ date[i]['dt']+unipol[i]['dt']
            dataset['train']['gt'] += rimes[i]['gt'] + biagini[i]['gt'] + washington[i]['gt'] + sinistri[i]['gt'] + unipol_train[i]['gt']+ date[i]['gt']+unipol[i]['gt']
            #dataset['train']['dt'] +=coco[i]['dt']+scene_icdar[i]['dt']#ocr[i]['dt']+ bentham[i]['dt'] + deutch[i]['dt'] + date[i]['dt'] + coco[i]['dt'] + scene_icdar[i]['dt'] #+ ocr[i]['dt']
            #dataset['train']['gt'] += coco[i]['gt']+scene_icdar[i]['gt']# ocr[i]['gt']+ bentham[i]['gt'] + deutch[i]['gt'] + date[i]['gt'] + coco[i]['gt'] + scene_icdar[i]['gt'] #+ ocr[i]['gt']


        dataset['test']['dt'] += iam["test"]['dt']
        dataset['test']['gt'] += iam["test"]['gt']

        dataset['train']['dt'] += iam["train"]['dt']
        dataset['train']['gt'] += iam["train"]['gt']

        dataset['test']['dt'] += brigantaggio["test"]['dt']
        dataset['test']['gt'] += brigantaggio["test"]['gt']

        dataset['train']['dt'] += brigantaggio["train"]['dt']
        dataset['train']['gt'] += brigantaggio["train"]['gt']

        dataset['test']['dt'] += verbali["test"]['dt']
        dataset['test']['gt'] += verbali["test"]['gt']

        dataset['train']['dt'] += verbali["train"]['dt']
        dataset['train']['gt'] += verbali["train"]['gt']

        #dataset['test']['dt'] += id_card["test"]['dt']
        #dataset['test']['gt'] += id_card["test"]['gt']

        #dataset['train']['dt'] += id_card["train"]['dt']
        #dataset['train']['gt'] += id_card["train"]['gt']

        #dataset['train']['gt'] += targhe['train']['gt']
        #dataset['train']['dt'] += targhe['train']['dt']

        #dataset['test']['dt'] += unipol["test"]['dt']
        #dataset['test']['gt'] += unipol["test"]['gt']


        #dataset['train']['dt'] += unipol["train"]['dt']
        #dataset['train']['gt'] += unipol["train"]['gt']

        #dataset['train']['dt'] += mlt2019["train"]['dt']# + sroie["train"]['dt']
        #dataset['train']['gt'] += mlt2019["train"]['gt']# + sroie["train"]['gt']

        #dataset['train']['dt']  +=   mlt2019["train"]['dt']+sroie["train"]['dt']#+synth["train"]['dt']
        #dataset['train']['gt']  +=   mlt2019["train"]['gt']+sroie["train"]['gt']#+synth["train"]['gt']

        #dataset['test']['dt'] += mlt2019["test"]['dt'] + sroie["test"]['dt'] #+ synth["test"]['dt']
        #dataset['test']['gt'] += mlt2019["test"]['gt'] + sroie["test"]['gt'] #+ synth["test"]['gt']

        dataset['valid']['dt'] = dataset['test']['dt']
        dataset['valid']['gt'] = dataset['test']['gt']
        '''
        print("Training elem:", len(dataset['train']['dt']))
        print("Training elem:", len(dataset['test']['dt']))

        return dataset
