from __future__ import print_function

import math
import os
import shutil
import stat
import subprocess
import sys
import argparse

import caffe
from caffe.model_libs import *
from google.protobuf import text_format


### Modify the following parameters accordingly ###
# The directory which contains the caffe code.
# We assume you are running the script at the CAFFE_ROOT.

caffe_root = os.path.expanduser('~/CAFFE')
CF_tool_root = os.path.expanduser('~/CF_tools')

default_job_name = "YOLO_tutu"
default_dataset_gen_dir = "{}/data/VOC0712".format(CF_tool_root)
default_model_weights = '{}/snapshot_models/YOLO/VGG_VOC0712_SSD_300x300_iter_120000.caffemodel'.format(CF_tool_root)
default_label_map = '{}/data/VOC0712/yolo/label_map.txt'.format(CF_tool_root)
default_img_size = 300
default_num_classes = 21

# Set true if you want to start training right after generating all files.
run_soon = True
# Set true if you want to load from most recently saved snapshot.
# Otherwise, we will load from the pretrain_model defined below.
resume_training = True
# If true, Remove old model files.
remove_old_models = False



def main(args):
    '''main '''
    #args.gen_dir_name = args.gen_dir.split('/')[-1]
    # The database file for training data. Created by data/VOC0712/create_data.sh
    train_data = "{}/lmdb/{}_trainval_lmdb".format(CF_tool_root, args.gen_dir)
    # The database file for testing data. Created by data/VOC0712/create_data.sh
    test_data = "{}/lmdb/{}_test_lmdb".format(CF_tool_root, args.gen_dir)


    # Specify the batch sampler.
    resize_width = args.image_resize
    resize_height = args.image_resize
    resize = "{}x{}".format(resize_width, resize_height)


    # Modify the job name if you want.
    job_name = "YOLO_{}_{}".format(args.gen_dir, resize)
    # The name of the model. Modify it if you want.
    model_name = "VGG_{}_{}".format(args.gen_dir, job_name)

    # Directory which stores the model .prototxt file.
    save_dir = "{}/models/{}".format(CF_tool_root, job_name)
    # Directory which stores the snapshot of models.
    snapshot_dir = "{}/snapshot_models/{}".format(CF_tool_root, job_name)
    # Directory which stores the job script and log file.
    job_dir = "{}/jobs/{}".format(CF_tool_root, job_name)
    # Directory which stores the detection results.
    output_result_dir = job_dir+'/predict_ss'

    # model definition files.
    train_net_file = "{}/train.prototxt".format(save_dir)
    test_net_file = "{}/test.prototxt".format(save_dir)
    deploy_net_file = "{}/deploy.prototxt".format(save_dir)
    solver_file = "{}/solver.prototxt".format(save_dir)
    # snapshot prefix.
    snapshot_prefix = "{}/{}".format(snapshot_dir, model_name)
    # job script path.
    job_file = "{}/{}.sh".format(job_dir, model_name)

    # Stores the test image names and sizes. Created by data/VOC0712/create_list.sh
    name_size_file = "{}/data/{}/yolo/test_name_size.txt".format(CF_tool_root, args.gen_dir)
    # The pretrained model. We use the Fully convolutional reduced (atrous) VGGNet.
    #pretrain_model = "{}/models/VGGNet/VGG_ILSVRC_16_layers_fc_reduced.caffemodel".format(CF_tool_root)
    #pretrain_model = "{}/snapshot_models/SSD_300x300/VGG_VOC0712_SSD_300x300_iter_120000.caffemodel".format(CF_tool_root)
    pretrain_model = args.model_weights
    # Stores LabelMapItem.
    label_map_file = args.labelmap_file
    #label_map_file = "{}/data/{}/ssd/label_map.txt".format(CF_tool_root, args.gen_dir)


    num_classes = int(args.num_classes)

    NUM_SIDE = 13
    NUM_OBJECT = 5
    NUM_OUTPUT = (num_classes+5)*NUM_OBJECT
    NUM_DIM = NUM_OUTPUT*NUM_SIDE*NUM_SIDE

    
    with open('{}/models/YoloVOC/darknet.prototxt'.format(CF_tool_root), 'r') as fin:
        with open(train_net_file, 'w') as fout:
            fout.write(fin.replace('NUM_OUTPUT', NUM_OUTPUT))
            fout.write(fin.replace('NUM_SHAPE_DIM', NUM_DIM))
            fout.write(fin.replace('NUM_SIDE', NUM_SIDE))
            fout.write(fin.replace('NUM_CLASSES', num_classes))
            fout.write(fin.replace('NUM_OBJECT', NUM_OBJECT))
            fout.write(fin.replace('TRAIN_BINARY', "{}/lmdb/{}_yolo_train.binaryproto".format(CF_tool_root, args.gen_dir)))
            fout.write(fin.replace('TEST_BINARY', "{}/lmdb/{}_yolo_test.binaryproto".format(CF_tool_root, args.gen_dir)))
            fout.write(fin.replace('TRAIN_LMDB', train_data))
            fout.write(fin.replace('TET_LMDB', test_data))
    # copy train.prototxt to test.prototxt
    shutil.copyfile(train_net_file, test_net_file)


    with open('{}/models/YoloVOC/solver.prototxt'.format(CF_tool_root), 'r') as fin:
        with open(solver_file, 'w') as fout:
            fout.write(fin.replace('DARKNET_NET', test_net_file))
            fout.write(fin.replace('TRAIN_NET', train_net_file))
            fout.write(fin.replace('TEST_NET', test_net_file))
            fout.write(fin.replace('SNAPSHOT_PREFIX', snapshot_prefix))

    with open('{}/models/YoloVOC/deploy.prototxt'.format(CF_tool_root), 'r') as fin:
        with open(deploy_net_file, 'w') as fout:
            fout.write(fin.replace('NUM_OUTPUT', NUM_OUTPUT))
            fout.write(fin.replace('NUM_SHAPE_DIM', NUM_DIM))
            fout.write(fin.replace('NUM_SIDE', NUM_SIDE))


    # Copy these files to job dir
    shutil.copy(train_net_file, job_dir)
    shutil.copy(test_net_file, job_dir)
    shutil.copy(deploy_net_file, job_dir)
    shutil.copy(solver_file, job_dir)



    # Solver parameters.
    # Defining which GPUs to use.
    gpus = "0"
    gpulist = gpus.split(",")
    num_gpus = len(gpulist)

    batch_size = 8
    accum_batch_size = 32
    iter_size = accum_batch_size / batch_size
    solver_mode = P.Solver.CPU
    device_id = 0
    batch_size_per_device = batch_size
    if num_gpus > 0:
        batch_size_per_device = int(math.ceil(float(batch_size) / num_gpus))
        iter_size = int(math.ceil(float(accum_batch_size) / (batch_size_per_device * num_gpus)))
        solver_mode = P.Solver.GPU
        device_id = int(gpulist[0])

    num_test_image = 4952
    test_batch_size = 8
    test_iter = int(math.ceil(float(num_test_image) / test_batch_size))


    solver_param = {
        'base_lr': 0.0005,
        'weight_decay': 0.0005,
        'lr_policy': "multistep",
        'stepvalue': [40000, 60000, 80000],
        'gamma': 0.1,
        'momentum': 0.9,
        'iter_size': iter_size,
        'max_iter': 80000,
        'snapshot': 5000,
        'display': 10,
        'average_loss': 10,
        'type': "SGD",
        'solver_mode': solver_mode,
        'device_id': device_id,
        'debug_info': False,
        'snapshot_after_train': True,

        'test_iter': [test_iter],
        'test_interval': 5000,
        'eval_type': "detection",
        'ap_version': "11point",
        'test_initialization': False,
        'show_per_class_result': True,
    }



    max_iter = 0
    for file in os.listdir(snapshot_dir):
      if file.endswith(".solverstate"):
        basename = os.path.splitext(file)[0]
        iter = int(basename.split("{}_iter_".format(model_name))[1])
        if iter > max_iter:
          max_iter = iter

    train_src_param = '--weights="{}" \\\n'.format(pretrain_model)
    if resume_training:
      if max_iter > 0:
        train_src_param = '--snapshot="{}_iter_{}.solverstate" \\\n'.format(snapshot_prefix, max_iter)


    if remove_old_models:
      for file in os.listdir(snapshot_dir):
        if file.endswith(".solverstate"):
          basename = os.path.splitext(file)[0]
          iter = int(basename.split("{}_iter_".format(model_name))[1])
          if max_iter > iter:
            os.remove("{}/{}".format(snapshot_dir, file))
        if file.endswith(".caffemodel"):
          basename = os.path.splitext(file)[0]
          iter = int(basename.split("{}_iter_".format(model_name))[1])
          if max_iter > iter:
            os.remove("{}/{}".format(snapshot_dir, file))


    import time
    timestamp = time.strftime('%Y%m%d%H%M%S')
    with open(job_file, 'w') as f:
        #f.write('cd {}\n'.format(caffe_root))
        f.write('{}/build/tools/caffe train \\\n'.format(caffe_root))
        f.write('--solver="{}" \\\n'.format(solver_file))
        f.write(train_src_param)
        if solver_param['solver_mode'] == P.Solver.GPU:
            f.write('--gpu {} 2>&1 | tee {}/{}_{}.log\n'.format(gpus, job_dir, model_name,timestamp))
        else:
            f.write('2>&1 | tee {}/{}_{}.log\n'.format(job_dir, model_name,timestamp))

    # Copy the python script to job_dir.
    py_file = os.path.abspath(__file__)
    shutil.copy(py_file, job_dir)

    # Run the job.
    print("Run file: {}".format(job_file))
    os.chmod(job_file, stat.S_IRWXU)
    if run_soon:
        subprocess.call(job_file, shell=True)


def parse_args():
    '''parse args'''
    parser = argparse.ArgumentParser()
    #parser.add_argument('--gpu_id', type=int, default=0, help='gpu id')
    parser.add_argument('--gen_dir', default=default_dataset_gen_dir)
    parser.add_argument('--image_resize', default=default_img_size, type=int)
    parser.add_argument('--model_weights', default=default_model_weights)
    parser.add_argument('--labelmap_file', default=default_label_map)
    parser.add_argument('--num_classes', default=default_num_classes)

    return parser.parse_args()


if __name__ == '__main__':
    main(parse_args())
