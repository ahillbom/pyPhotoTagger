import cv2
import cvlib as cv
from cvlib.object_detection import draw_bbox
import json
import piexif
import piexif.helper
import argparse

class ObjectDetector():
    def __init__(self, filename):
        self.filename = filename

    def load_photo(self):
        self.img_input = cv2.imread(self.filename)

    def detect_objects(self):
        self.bboxs, self.labels, self.confds = cv.detect_common_objects(self.img_input)

    def draw_boundboxes(self):
        self.img_boundboxes = draw_bbox(self.img_input, self.bboxs, self.labels, self.confds)

    def pack_todict(self, decimals = 2):
        self.objects = {}
        for label, conf in zip(self.labels, self.confds):
            self.objects.setdefault(label, []).append(round(conf, decimals))
        return self.objects

    def get_objects_str(self, delimiter = ","):
        objects_str = ""
        for object_str in self.objects.keys():
            objects_str += object_str + delimiter
        return objects_str

    def print_objects(self):
        json_object = json.dumps(self.objects, indent = 4)
        print(json_object)

class ExifMod():
    def __init__(self, filename):
        self.objects = {}
        self.filename = filename

    def load(self):
        self.exif_dict = piexif.load(self.filename)

    def write(self):
        piexif.insert(piexif.dump(self.exif_dict), self.filename)

    def _encode_xpkeywords(self, s):
        b = s.encode('utf-16-le') + b'\x00\x00'
        return tuple([int(i) for i in b])

    def add_usercomment(self, comment):
        self.exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(comment, encoding="unicode")

    def add_keywords(self, keywords):
        self.exif_dict["0th"][piexif.ImageIFD.XPKeywords] = self._encode_xpkeywords(keywords)

class Photo():
    def __init__(self, filename):
        self.filename = filename

    def detect_objects(self):
        objdetector = ObjectDetector(self.filename)
        objdetector.load_photo()
        objdetector.detect_objects()
        self.objects = objdetector.pack_todict()
        self.objects_str = objdetector.get_objects_str()

    def update_exif(self):
        exif = ExifMod(self.filename)
        exif.load()
        exif.add_keywords(self.objects_str)
        exif.add_usercomment(json.dumps(self.objects))
        exif.write()

def InitArgParser():
    argparser = argparse.ArgumentParser(description='PhotoTagger - uses Machine Learning to detect objects in photos. \
        PhotoTagger adds keywords and other information to JPEG metadata based on the objects detected.')

    argparser.add_argument('-f', '--filename', dest='filename', type=str, help='Photo filename', default=False)
    return argparser.parse_args()

args = InitArgParser()

photo = Photo(args.filename)
photo.detect_objects()
photo.update_exif()