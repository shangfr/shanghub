# -*- coding: utf-8 -*-
"""
Created on Tue Jul 13 10:22:12 2021

@author: shangfr
"""

import dlib
from imageio import imread
import glob

detector = dlib.get_frontal_face_detector()
win = dlib.image_window()
paths = glob.glob('faces/*.jpg')

for path in paths:
	img = imread(path)
	# 1 表示将图片放大一倍，便于检测到更多人脸
	dets = detector(img, 1)
	print('检测到了 %d 个人脸' % len(dets))
	for i, d in enumerate(dets):
		print('- %d：Left %d Top %d Right %d Bottom %d' % (i, d.left(), d.top(), d.right(), d.bottom()))

	win.clear_overlay()
	win.set_image(img)
	win.add_overlay(dets)
	dlib.hit_enter_to_continue()
    
    
# 设定参数  
path = 'faces/12.jpg'
img = imread(path)
# -1 表示人脸检测的判定阈值
# scores 为每个检测结果的得分，idx 为人脸检测器的类型
dets, scores, idx = detector.run(img, 1, -1)
for i, d in enumerate(dets):
	print('%d：score %f, face_type %f' % (i, scores[i], idx[i]))
win = dlib.image_window()
win.clear_overlay()
win.set_image(img)
win.add_overlay(dets)
dlib.hit_enter_to_continue()




# 关键点检测
predictor_path = 'shape_predictor_68_face_landmarks.dat'
predictor = dlib.shape_predictor(predictor_path)
win = dlib.image_window()
paths = glob.glob('faces/*.jpg')

for path in paths:
	img = imread(path)
	win.clear_overlay()
	win.set_image(img)

	# 1 表示将图片放大一倍，便于检测到更多人脸
	dets = detector(img, 1)
	print('检测到了 %d 个人脸' % len(dets))
	for i, d in enumerate(dets):
		print('- %d: Left %d Top %d Right %d Bottom %d' % (i, d.left(), d.top(), d.right(), d.bottom()))
		shape = predictor(img, d)
		# 第 0 个点和第 1 个点的坐标
		print('Part 0: {}, Part 1: {}'.format(shape.part(0), shape.part(1)))
		win.add_overlay(shape)

	win.add_overlay(dets)
	dlib.hit_enter_to_continue()


#加载库

# -*- coding: utf-8 -*-

import dlib
from imageio import imread
import glob
import numpy as np
#准备好模型和图片

detector = dlib.get_frontal_face_detector()
predictor_path = 'shape_predictor_68_face_landmarks.dat'
predictor = dlib.shape_predictor(predictor_path)
face_rec_model_path = 'dlib_face_recognition_resnet_model_v1.dat'
facerec = dlib.face_recognition_model_v1(face_rec_model_path)
labeled = glob.glob('labeled/*.jpg')
labeled_data = {}
unlabeled = glob.glob('unlabeled/*.jpg')
#距离计算函数

# 定义一个计算Euclidean距离的函数
def distance(a, b):
	# d = 0
	# for i in range(len(a)):
	# 	d += (a[i] - b[i]) * (a[i] - b[i])
	# return np.sqrt(d)
	return np.linalg.norm(np.array(a) - np.array(b), ord=2)
#获取标注图片对应的向量表示

# 读取标注图片并保存对应的128向量
for path in labeled:
	img = imread(path)
	name = path.split('/')[1].rstrip('.jpg')
	dets = detector(img, 1)
	# 这里假设每张图只有一个人脸
	shape = predictor(img, dets[0])
	face_vector = facerec.compute_face_descriptor(img, shape)
	labeled_data[name] = face_vector
#将未标注图片的向量表示，和标注图片逐一匹配

# 读取未标注图片，并和标注图片进行对比
for path in unlabeled:
	img = imread(path)
	name = path.split('/')[1].rstrip('.jpg')
	dets = detector(img, 1)
	# 这里假设每张图只有一个人脸
	shape = predictor(img, dets[0])
	face_vector = facerec.compute_face_descriptor(img, shape)
	matches = []
	for key, value in labeled_data.items():
		d = distance(face_vector, value)
		if d < 0.6:
			matches.append(key + ' %.2f' % d)
	print('{}：{}'.format(name, ';'.join(matches)))


#人脸聚类
#对于大量图片中的大量人脸，基于以上人脸识别标准进行聚类，把距离较近的人脸聚为一类，即有可能为同一个人

#加载库

# -*- coding: utf-8 -*-

import dlib
from imageio import imread
import glob
import os
from collections import Counter
#准备好模型和图片

detector = dlib.get_frontal_face_detector()
predictor_path = 'shape_predictor_68_face_landmarks.dat'
predictor = dlib.shape_predictor(predictor_path)
face_rec_model_path = 'dlib_face_recognition_resnet_model_v1.dat'
facerec = dlib.face_recognition_model_v1(face_rec_model_path)
paths = glob.glob('faces/*.jpg')
#获取所有图片的关键点检测结果和向量表示

vectors = []
images = []
for path in paths:
	img = imread(path)
	dets = detector(img, 1)
	for i, d in enumerate(dets):
		shape = predictor(img, d)
		face_vector = facerec.compute_face_descriptor(img, shape)
		vectors.append(face_vector)
		images.append((img, shape))
#以0.5为阈值进行聚类，并找出人脸数量最多的类

labels = dlib.chinese_whispers_clustering(vectors, 0.5)
num_classes = len(set(labels))
print('共聚为 %d 类' % num_classes)
biggest_class = Counter(labels).most_common(1)
print(biggest_class)
#将最大类中包含的人脸保存下来，类似的也可以处理其他的类

output_dir = 'most_common'
if not os.path.exists(output_dir):
	os.mkdir(output_dir)
face_id = 1
for i in range(len(images)):
	if labels[i] == biggest_class[0][0]:
		img, shape = images[i]
		dlib.save_face_chip(img, shape, output_dir + '/face_%d' % face_id, size=150, padding=0.25)
		face_id += 1
#物体追踪
#物体追踪是指，对于视频文件，在第一帧指定一个矩形区域，对于后续帧自动追踪和更新区域的位置

#加载库

# -*- coding: utf-8 -*-

import dlib
from imageio import imread
import glob
#准备好追踪器和图片

tracker = dlib.correlation_tracker()
win = dlib.image_window()
paths = sorted(glob.glob('video_frames/*.jpg'))
#追踪图片中的物体

for i, path in enumerate(paths):
	img = imread(path)
	# 第一帧，指定一个区域
	if i == 0:
		tracker.start_track(img, dlib.rectangle(74, 67, 112, 153))
	# 后续帧，自动追踪
	else:
		tracker.update(img)

	win.clear_overlay()
	win.set_image(img)
	win.add_overlay(tracker.get_position())
	dlib.hit_enter_to_continue()
#尽管物体的位置在不断变化，Dlib始终能够比较准确地进行追踪



import face_recognition
image = face_recognition.load_image_file('faces/12.jpg')
face_locations = face_recognition.face_locations(image)

face_landmarks_list = face_recognition.face_landmarks(image)

known_image = face_recognition.load_image_file("faces/12.jpg")
unknown_image = face_recognition.load_image_file("faces/124.jpg")

biden_encoding = face_recognition.face_encodings(known_image)[0]
unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

results = face_recognition.compare_faces([biden_encoding], unknown_encoding)

