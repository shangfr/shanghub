# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 15:33:04 2019

@author: ShangFR
"""
import paddlehub as hub

# 图像识别    

module = hub.Module(module_dir=['modules\\resnet_v2_50_imagenet'])
print('Model loaded.')

def model_predict(img_path):
    # set input dict
    input_dict = {"image": [img_path]}
    #results = model.object_detection(data=input_dict)
    results = module.classification(data=input_dict)
    return results

