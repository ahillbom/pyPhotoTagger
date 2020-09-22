### What is this?
This app detects objects in photos using Computer Vision and automatically adds keywords to JPEG Exif metadata. The keywords are sorted by the area of objects. It can tag a single photo, or recursively tag photos in a directory. The app is written in Python and is based on an open-source Computer Vision library  [cvlib](https://github.com/arunponnusamy/cvlib) from [arunponnusamy](https://github.com/arunponnusamy). The library uses a [pre-trained YOLO v3 model](https://pjreddie.com/darknet/yolo/), which is capable of detecting 80 different objects.

### Dependencies
* [OpenCV](https://pypi.org/project/opencv-python/)
* [TensorFlow](https://pypi.org/project/tensorflow/)
* [Piexif](https://pypi.org/project/piexif/)
* [cvlib](https://github.com/arunponnusamy/cvlib)

```
pip install opencv-python tensorflow cvlib piexif
```
### How to use?

Detect objects and add keywords to `example.jpg`.
```
pyphototagger.py -f example.jpg
```
Detect objects and add keywords to `example.jpg` with verbose output.
```
pyphototagger.py -v -f example.jpg
```
Detect objects and add keywords to all `*.jpg` and `*.jpeg` files recursively found in `example/photos` directory.
```
pyphototagger.py -d example/photos
```
Print help
```
pyphototagger.py -h
```
