import sys
import os
import cv2
import cvlib as cv
from cvlib.object_detection import draw_bbox
import json
import piexif
import piexif.helper
import argparse
import glob
import logging

### Classes

class Object():
    def __init__(self, bbox, label, conf):
        self.bbox = bbox
        self.label = label
        self.conf = conf
        self.area = (bbox[2] - bbox[0])*(bbox[3] - bbox[1])

    def get_bbox(self):
        return self.bbox

    def get_label(self):
        return self.label

    def get_conf(self):
        return self.conf

    def get_area(self):
        return self.area

class Objects():
    def __init__(self, parent_height, parent_width):
        self.objects = []
        self.parent_height = parent_height
        self.parent_width = parent_width
        self.parent_area = parent_height * parent_width

    def add(self, bbox, label, conf):
        obj = Object(bbox, label, conf)
        self.objects.append(obj)

    def get_dict(self, decimals = 2):
        objects_dict = {}
        for obj in self.objects:
            objects_dict.setdefault(obj.label, []).append([round(obj.conf, decimals), obj.area])
        return objects_dict

    def get_by_label(self, label):
        objs = []
        for obj in self.objects:
            if obj.get_label() == label:
                objs.append(obj)
        return objs

    def get_labels(self):
        labels = []
        for obj in self.objects:
            labels.append(obj.get_label())
        return labels

    def get_labels_unique(self):
        labels = self.get_labels()
        return list(dict.fromkeys(labels))

    def get_labels_unique_area_rel(self):
        areas = dict()
        for label in self.get_labels_unique():
            area_rel = 0
            for obj in self.get_by_label(label):
                area_rel += obj.get_area() / self.parent_area
            areas[label] = area_rel
        return areas

    def get_labels_sorted_by_area(self):
        labels = self.get_labels_unique_area_rel()
        labels = sorted(labels.items(), key=lambda x: x[1], reverse=True)
        result = []
        for label in labels:
            result.append(label[0])
        return result

    def get_labels_as_keywords_str(self, delimiter = ","):
        keywords = ""
        labels = self.get_labels_sorted_by_area()
        for label in labels:
            keywords += label + delimiter
        # Remove last delimiter
        if len(keywords) > 0:
            keywords = keywords[:-1]
        return keywords

class ObjectDetector():
    def __init__(self, filename):
        self.filename = filename

    def __draw_boundboxes(self):
        self.img_boundboxes = draw_bbox(self.img_input, self.bboxs, self.labels, self.confds)

    def load(self):
        self.img_input = cv2.imread(self.filename)
        self.height, self.width = self.img_input.shape[:2]
        self.objects = Objects(self.height, self.width)

    def detect_objects(self, decimals = 2):
        self.bboxs, self.labels, self.confds = cv.detect_common_objects(self.img_input)
        for bbox, label, confds in zip(self.bboxs, self.labels, self.confds):
            self.objects.add(bbox, label, confds)
        return self.objects

    def get_objects(self):
        return self.objects

class ExifMod():
    def __init__(self, filename):
        self.objects = {}
        self.filename = filename

    def _encode_xpkeywords(self, s):
        b = s.encode('utf-16-le') + b'\x00\x00'
        return tuple([int(i) for i in b])

    def load(self):
        self.exif_dict = piexif.load(self.filename)

    def write(self):
        piexif.insert(piexif.dump(self.exif_dict), self.filename)

    def add_usercomment(self, comment):
        self.exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(comment, encoding="unicode")

    def add_keywords(self, keywords):
        self.exif_dict["0th"][piexif.ImageIFD.XPKeywords] = self._encode_xpkeywords(keywords)

class Image():
    def __init__(self, filename):
        self.filename = filename

    def detect_objects(self):
        objdetector = ObjectDetector(self.filename)
        objdetector.load()
        self.objects = objdetector.detect_objects()

    def get_keywords_str(self):
        return self.objects.get_labels_as_keywords_str()

    def update_exif(self):
        exif = ExifMod(self.filename)
        exif.load()
        exif.add_keywords(self.get_keywords_str())
        #exif.add_usercomment(json.dumps(self.keywords_str))
        exif.write()

### Functions

def init_arg_parser():
    argparser = argparse.ArgumentParser(description='This app detects objects in photos using Computer Vision and \
        automatically adds keywords to JPEG Exif metadata. The keywords are sorted by the area of objects. \
        It can tag a single photo, or recursively tag photos in a directory.')

    argparser.add_argument('-f', dest='filename', type=str, help='Detect objects and add keywords to this file.')
    argparser.add_argument('-d', dest='dir', type=str, help='Detect objects and add keywords to all *.jpg and *.jpeg \
        files recursively found in this directory.')
    argparser.add_argument('-v', dest='verbose', action='store_true', help='Verbose output.')
    return argparser.parse_args()

def init_logger():
    logger.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(message)s')

    logger_stdout = logging.StreamHandler(sys.stdout)
    logger_stdout.setLevel(logging.DEBUG)
    logger_stdout.setFormatter(formatter)
    logger.addHandler(logger_stdout)

def find_photo_files(path):
    extensions = [ ".[jJ][pP][gG]", ".[jJ][pP][eE][gG]" ]
    files = []
    for extension in extensions:
        for f in glob.glob(path + "**/*" + extension, recursive=True):
            files.append(f)
    return files

def process_file(filename):
    logger.info('Processing {0}'.format(filename) )
    image = Image(filename)
    image.detect_objects()
    image.update_exif()
    logger.info('Found {0}'.format(image.get_keywords_str()))

def process_dir(path):
    files = find_photo_files(args.dir)
    for file in files:
        process_file(file)

logger = logging.getLogger()
args = init_arg_parser()

if args.verbose == True:
    init_logger()
    logger.setLevel(logging.INFO)

if args.filename != None:
    process_file(args.filename)
    sys.exit()

if args.dir != None:
    process_dir(args.dir)
    sys.exit()