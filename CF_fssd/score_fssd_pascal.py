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
#caffe_root = os.getcwd()
caffe_root = "/home/ps/CAFFE_SSD"
#CF_tool_root = "/home/ps/CF_tools"

CF_tool_root = "/media/ps/AAA/CF_tools"
default_job_name = "FSSD_tutu_300x300"
default_dataset_gen_dir = "VOC0712"
default_label_map = '{}/data/VOC0712/ssd/label_map.txt'.format(CF_tool_root)
default_img_size = 300


# Add extra layers on top of a "base" network (e.g. VGGNet or Inception).
def AddExtraLayers(net, use_batchnorm=False, lr_mult=1):
    use_relu = True
    # Not really sure what use_batchnorm means.
    # It's different than ssd file

    # Add additional convolutional layers.
    # 19 x 19
    from_layer = net.keys()[-1]

    # Fuse features from layer conv4_3
    # In original paper, the layer which we want to fuse features (eg. conv4_3) followed by a 3x3 conv layer to extract features better before fusion.
    # There's no that layer here
    # This step is to reduce dimension (by applying a 1x1 kernel on top of conv4_3)
    # Output also the final fusion feature map
    ConvBNLayer(net, "conv4_3",  "conv4_3_reduce", use_batchnorm, use_relu, 256, 1, 0, 1,
                lr_mult=lr_mult)
    # In original paper, if we want to extract features from multiple layers (eg. conv4_3, conv5_3), we must make them the same size.
    # This could be done by applied a deconv layer on top of conv5_3

    # Apply on top of the last layer
    # TODO(weiliu89): Construct the name using the last layer to avoid duplication.
    # 10 x 10
    out_layer = "conv6_1"
    ConvBNLayer(net, from_layer, out_layer, use_batchnorm, use_relu, 256, 1, 0, 1,
                lr_mult=lr_mult)

    from_layer = out_layer
    out_layer = "conv6_2"
    ConvBNLayer(net, from_layer, out_layer, use_batchnorm, use_relu, 512, 3, 1, 1,
                lr_mult=lr_mult)

    # 5 x 5
    from_layer = out_layer
    out_layer = "conv7_1"
    ConvBNLayer(net, from_layer, out_layer, use_batchnorm, use_relu, 128, 1, 0, 1,
                lr_mult=lr_mult)

    from_layer = out_layer
    out_layer = "conv7_2"
    ConvBNLayer(net, from_layer, out_layer, use_batchnorm, use_relu, 256, 3, 1, 2,
                lr_mult=lr_mult)

    # Compared with ssd model, this code has less feature extractor layers

    # Similar to line 42 (for dimension reduction)
    ConvBNLayer(net, "fc7",  "fc7_reduce", use_batchnorm, use_relu, 256, 1, 0, 1,
                lr_mult=lr_mult)

    # This is to resize fc7_us and conv7_2_us layer to concat with conv4_3_reduce (fusion FM produced from conv4_3)
    net['fc7_us'] = L.Interp(net['fc7_reduce'], interp_param={
                             'height': 38, 'width': 38})

    net['conv7_2_us'] = L.Interp(net['conv7_2'], interp_param={
                                 'height': 38, 'width': 38})

    # Now concat.
    # According to the paper, this is element-sum module, whereas the weights are applied manually.
    net['fea_concat'] = L.Concat(
        net['conv4_3_reduce'], net['fc7_us'], net['conv7_2_us'], axis=1)

    # And followed by a normalization layer
    # In original paper, the batch norm layer is applied on top of every child fusion fmap BEFORE concating with different scales.
    # This probably to reduce computational loss
    net['fea_concat_bn'] = L.BatchNorm(net['fea_concat'], in_place=True)

    # Some layers not reallly sure what for...
    # Probably just to learn features betters??
    ConvBNLayer(net, 'fea_concat_bn', 'fea_concat_bn_ds_1',
                use_batchnorm, use_relu, 512, 3, 1, 1, lr_mult=lr_mult)
    ConvBNLayer(net, 'fea_concat_bn_ds_1', 'fea_concat_bn_ds_2',
                use_batchnorm, use_relu, 512, 3, 1, 2, lr_mult=lr_mult)
    ConvBNLayer(net, 'fea_concat_bn_ds_2', 'fea_concat_bn_ds_4',
                use_batchnorm, use_relu, 256, 3, 1, 2, lr_mult=lr_mult)
    ConvBNLayer(net, 'fea_concat_bn_ds_4', 'fea_concat_bn_ds_8',
                use_batchnorm, use_relu, 256, 3, 1, 2, lr_mult=lr_mult)
    ConvBNLayer(net, 'fea_concat_bn_ds_8', 'fea_concat_bn_ds_16',
                use_batchnorm, use_relu, 256, 3, 0, 1, lr_mult=lr_mult)
    ConvBNLayer(net, 'fea_concat_bn_ds_16', 'fea_concat_bn_ds_32',
                use_batchnorm, use_relu, 256, 3, 0, 1, lr_mult=lr_mult)
    return net


# Set true if you want to start training right after generating all files.
run_soon = True
# Set true if you want to load from most recently saved snapshot.
# Otherwise, we will load from the pretrain_model defined below.
resume_training = True
# If true, Remove old model files.
remove_old_models = False


def main(args):
    '''main '''

    # The database file for training data. Created by data/VOC0712/create_data.sh
    train_data = "{}/lmdb/{}_trainval_lmdb".format(CF_tool_root, args.gen_dir)
    # The database file for testing data. Created by data/VOC0712/create_data.sh
    test_data = "{}/lmdb/{}_test_lmdb".format(CF_tool_root, args.gen_dir)

    # Specify the batch sampler.
    resize_width = args.image_resize
    resize_height = args.image_resize
    resize = "{}x{}".format(resize_width, resize_height)

    batch_sampler = [
        {
            'sampler': {
            },
            'max_trials': 1,
            'max_sample': 1,
        },
        {
            'sampler': {
                'min_scale': 0.3,
                'max_scale': 1.0,
                'min_aspect_ratio': 0.5,
                'max_aspect_ratio': 2.0,
            },
            'sample_constraint': {
                'min_jaccard_overlap': 0.1,
            },
            'max_trials': 50,
            'max_sample': 1,
        },
        {
            'sampler': {
                'min_scale': 0.3,
                'max_scale': 1.0,
                'min_aspect_ratio': 0.5,
                'max_aspect_ratio': 2.0,
            },
            'sample_constraint': {
                'min_jaccard_overlap': 0.3,
            },
            'max_trials': 50,
            'max_sample': 1,
        },
        {
            'sampler': {
                'min_scale': 0.3,
                'max_scale': 1.0,
                'min_aspect_ratio': 0.5,
                'max_aspect_ratio': 2.0,
            },
            'sample_constraint': {
                'min_jaccard_overlap': 0.5,
            },
            'max_trials': 50,
            'max_sample': 1,
        },
        {
            'sampler': {
                'min_scale': 0.3,
                'max_scale': 1.0,
                'min_aspect_ratio': 0.5,
                'max_aspect_ratio': 2.0,
            },
            'sample_constraint': {
                'min_jaccard_overlap': 0.7,
            },
            'max_trials': 50,
            'max_sample': 1,
        },
        {
            'sampler': {
                'min_scale': 0.3,
                'max_scale': 1.0,
                'min_aspect_ratio': 0.5,
                'max_aspect_ratio': 2.0,
            },
            'sample_constraint': {
                'min_jaccard_overlap': 0.9,
            },
            'max_trials': 50,
            'max_sample': 1,
        },
        {
            'sampler': {
                'min_scale': 0.3,
                'max_scale': 1.0,
                'min_aspect_ratio': 0.5,
                'max_aspect_ratio': 2.0,
            },
            'sample_constraint': {
                'max_jaccard_overlap': 1.0,
            },
            'max_trials': 50,
            'max_sample': 1,
        },
    ]
    train_transform_param = {
        'mirror': True,
        'mean_value': [104, 117, 123],
        'resize_param': {
            'prob': 1,
            'resize_mode': P.Resize.WARP,
            'height': resize_height,
            'width': resize_width,
            'interp_mode': [
                P.Resize.LINEAR,
                P.Resize.AREA,
                P.Resize.NEAREST,
                P.Resize.CUBIC,
                P.Resize.LANCZOS4,
            ],
        },
        'distort_param': {
            'brightness_prob': 0.5,
            'brightness_delta': 32,
            'contrast_prob': 0.5,
            'contrast_lower': 0.5,
            'contrast_upper': 1.5,
            'hue_prob': 0.5,
            'hue_delta': 18,
            'saturation_prob': 0.5,
            'saturation_lower': 0.5,
            'saturation_upper': 1.5,
            'random_order_prob': 0.0,
        },
        'expand_param': {
            'prob': 0.5,
            'max_expand_ratio': 4.0,
        },
        'emit_constraint': {
            'emit_type': caffe_pb2.EmitConstraint.CENTER,
        }
    }
    test_transform_param = {
        'mean_value': [104, 117, 123],
        'resize_param': {
            'prob': 1,
            'resize_mode': P.Resize.WARP,
            'height': resize_height,
            'width': resize_width,
            'interp_mode': [P.Resize.LINEAR],
        },
    }


    # If true, use batch norm for all newly added layers.
    # Currently only the non batch norm version has been tested.
    use_batchnorm = False
    lr_mult = 2
    if use_batchnorm:
        base_lr = 0.0004
    else:
        base_lr = 0.00004/10


    # Modify the job name if you want.
    job_name = "FSSD_{}_{}".format(args.gen_dir, resize)
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


    # Find most recent snapshot.
    max_iter = 0
    for file in os.listdir(snapshot_dir):
        if file.endswith(".caffemodel"):
            basename = os.path.splitext(file)[0]
            iter = int(basename.split("{}_iter_".format(model_name))[1])
            if iter > max_iter:
                max_iter = iter

    if max_iter == 0:
        print("Cannot find snapshot in {}".format(snapshot_dir))
        sys.exit()


    # Stores the test image names and sizes. Created by data/VOC0712/create_list.sh
    name_size_file = "{}/data/{}/ssd/test_name_size.txt".format(CF_tool_root, args.gen_dir)
    # The resume model.
    pretrain_model = "{}_iter_{}.caffemodel".format(snapshot_prefix, max_iter)
    # Stores LabelMapItem.
    label_map_file = args.labelmap_file
    #label_map_file = "{}/data/{}/ssd/label_map.txt".format(CF_tool_root, args.gen_dir)


    # MultiBoxLoss parameters.
    num_classes = 21
    share_location = True
    background_label_id=0
    train_on_diff_gt = True
    normalization_mode = P.Loss.VALID
    code_type = P.PriorBox.CENTER_SIZE
    ignore_cross_boundary_bbox = False
    mining_type = P.MultiBoxLoss.MAX_NEGATIVE
    neg_pos_ratio = 3.
    loc_weight = (neg_pos_ratio + 1.) / 4.
    multibox_loss_param = {
        'loc_loss_type': P.MultiBoxLoss.SMOOTH_L1,
        'conf_loss_type': P.MultiBoxLoss.SOFTMAX,
        'loc_weight': loc_weight,
        'num_classes': num_classes,
        'share_location': share_location,
        'match_type': P.MultiBoxLoss.PER_PREDICTION,
        'overlap_threshold': 0.5,
        'use_prior_for_matching': True,
        'background_label_id': background_label_id,
        'use_difficult_gt': train_on_diff_gt,
        'mining_type': mining_type,
        'neg_pos_ratio': neg_pos_ratio,
        'neg_overlap': 0.5,
        'code_type': code_type,
        'ignore_cross_boundary_bbox': ignore_cross_boundary_bbox,
    }
    loss_param = {
        'normalization': normalization_mode,
    }

    # parameters for generating priors.
    # minimum dimension of input image
    min_dim = 300
    mbox_source_layers = ['fea_concat_bn_ds_1','fea_concat_bn_ds_2','fea_concat_bn_ds_4','fea_concat_bn_ds_8','fea_concat_bn_ds_16','fea_concat_bn_ds_32']
    # in percent %
    min_ratio = 20
    max_ratio = 90
    step = int(math.floor((max_ratio - min_ratio) / (len(mbox_source_layers) - 2)))
    min_sizes = []
    max_sizes = []
    for ratio in xrange(min_ratio, max_ratio + 1, step):
        min_sizes.append(min_dim * ratio / 100.)
        max_sizes.append(min_dim * (ratio + step) / 100.)

    min_sizes = [min_dim * 10 / 100.] + min_sizes
    max_sizes = [min_dim * 20 / 100.] + max_sizes
    steps = []
    aspect_ratios = [[2],[2,3],[2,3],[2],[2],[2]]
    normalizations = [-1,-1,-1,-1,-1,-1]
    """
    steps = [8, 16, 32, 64, 100, 300]
    aspect_ratios = [[2], [2, 3], [2, 3], [2, 3], [2], [2]]
    # L2 normalize conv4_3.
    normalizations = [20, -1, -1, -1, -1, -1]
    """
    
    # variance used to encode/decode prior bboxes.
    if code_type == P.PriorBox.CENTER_SIZE:
        prior_variance = [0.1, 0.1, 0.2, 0.2]
    else:
        prior_variance = [0.1]
    flip = True
    clip = False

    # Solver parameters.
    # Defining which GPUs to use.
    gpus = "0"
    gpulist = gpus.split(",")
    num_gpus = len(gpulist)

    # The number does not matter since we do not do training with this script.
    batch_size = 1
    accum_batch_size = 1
    iter_size = accum_batch_size / batch_size
    solver_mode = P.Solver.CPU
    device_id = 0
    batch_size_per_device = batch_size
    if num_gpus > 0:
        batch_size_per_device = int(math.ceil(float(batch_size) / num_gpus))
        iter_size = int(math.ceil(float(accum_batch_size) / (batch_size_per_device * num_gpus)))
        solver_mode = P.Solver.GPU
        device_id = int(gpulist[0])

    if normalization_mode == P.Loss.NONE:
        base_lr /= batch_size_per_device
    elif normalization_mode == P.Loss.VALID:
        base_lr *= 25. / loc_weight
    elif normalization_mode == P.Loss.FULL:
        # Roughly there are 2000 prior bboxes per image.
        # TODO(weiliu89): Estimate the exact # of priors.
        base_lr *= 2000.

    # Evaluate on whole test set.
    num_test_image = 4952
    test_batch_size = 8
    # Ideally test_batch_size should be divisible by num_test_image,
    # otherwise mAP will be slightly off the true value.
    test_iter = int(math.ceil(float(num_test_image) / test_batch_size))

    solver_param = {
        # Train parameters
        'base_lr': base_lr,
        'weight_decay': 0.0005,
        'lr_policy': "multistep",
        'stepvalue': [80000, 100000, 120000],
        'gamma': 0.1,
        'momentum': 0.9,
        'iter_size': iter_size,
        'max_iter': 0,
        'snapshot': 0,
        'display': 10,
        'average_loss': 10,
        'type': "SGD",
        'solver_mode': solver_mode,
        'device_id': device_id,
        'debug_info': False,
        'snapshot_after_train': False,
        # Test parameters
        'test_iter': [test_iter],
        'test_interval': 10000,
        'eval_type': "detection",
        'ap_version': "11point",
        'test_initialization': True,
    }

    # parameters for generating detection output.
    det_out_param = {
        'num_classes': num_classes,
        'share_location': share_location,
        'background_label_id': background_label_id,
        'nms_param': {'nms_threshold': 0.45, 'top_k': 400},
        'save_output_param': {
            'output_directory': output_result_dir,
            'output_name_prefix': "comp4_det_test_",
            'output_format': "VOC",
            'label_map_file': label_map_file,
            'name_size_file': name_size_file,
            'num_test_image': num_test_image,
        },
        'keep_top_k': 200,
        'confidence_threshold': 0.01,
        'code_type': code_type,
    }

    # parameters for evaluating detection results.
    det_eval_param = {
        'num_classes': num_classes,
        'background_label_id': background_label_id,
        'overlap_threshold': 0.5,
        'evaluate_difficult_gt': False,
        'name_size_file': name_size_file,
    }

    ### Hopefully you don't need to change the following ###
    # Check file.
    check_if_exist(train_data)
    check_if_exist(test_data)
    check_if_exist(label_map_file)
    check_if_exist(pretrain_model)
    make_if_not_exist(save_dir)
    make_if_not_exist(job_dir)
    make_if_not_exist(snapshot_dir)

    # Create train net.
    net = caffe.NetSpec()
    net.data, net.label = CreateAnnotatedDataLayer(train_data, batch_size=batch_size_per_device,
                                                   train=True, output_label=True, label_map_file=label_map_file,
                                                   transform_param=train_transform_param, batch_sampler=batch_sampler)

    VGGNetBody(net, from_layer='data', fully_conv=True, reduced=True, dilated=True,
               dropout=False)

    AddExtraLayers(net, use_batchnorm, lr_mult=lr_mult)

    mbox_layers = CreateMultiBoxHead(net, data_layer='data', from_layers=mbox_source_layers,
                                     use_batchnorm=use_batchnorm, min_sizes=min_sizes, max_sizes=max_sizes,
                                     aspect_ratios=aspect_ratios, steps=steps, normalizations=normalizations,
                                     num_classes=num_classes, share_location=share_location, flip=flip, clip=clip,
                                     prior_variance=prior_variance, kernel_size=3, pad=1, lr_mult=lr_mult)

    # Create the MultiBoxLossLayer.
    name = "mbox_loss"
    mbox_layers.append(net.label)
    net[name] = L.MultiBoxLoss(*mbox_layers, multibox_loss_param=multibox_loss_param,
                               loss_param=loss_param, include=dict(
                                   phase=caffe_pb2.Phase.Value('TRAIN')),
                               propagate_down=[True, True, False, False])

    with open(train_net_file, 'w') as f:
        print('name: "{}_train"'.format(model_name), file=f)
        print(net.to_proto(), file=f)
    shutil.copy(train_net_file, job_dir)

    # Create test net.
    net = caffe.NetSpec()
    net.data, net.label = CreateAnnotatedDataLayer(test_data, batch_size=test_batch_size,
                                                   train=False, output_label=True, label_map_file=label_map_file,
                                                   transform_param=test_transform_param)

    VGGNetBody(net, from_layer='data', fully_conv=True, reduced=True, dilated=True,
               dropout=False)

    AddExtraLayers(net, use_batchnorm, lr_mult=lr_mult)

    mbox_layers = CreateMultiBoxHead(net, data_layer='data', from_layers=mbox_source_layers,
                                     use_batchnorm=use_batchnorm, min_sizes=min_sizes, max_sizes=max_sizes,
                                     aspect_ratios=aspect_ratios, steps=steps, normalizations=normalizations,
                                     num_classes=num_classes, share_location=share_location, flip=flip, clip=clip,
                                     prior_variance=prior_variance, kernel_size=3, pad=1, lr_mult=lr_mult)

    conf_name = "mbox_conf"
    if multibox_loss_param["conf_loss_type"] == P.MultiBoxLoss.SOFTMAX:
        reshape_name = "{}_reshape".format(conf_name)
        net[reshape_name] = L.Reshape(
            net[conf_name], shape=dict(dim=[0, -1, num_classes]))
        softmax_name = "{}_softmax".format(conf_name)
        net[softmax_name] = L.Softmax(net[reshape_name], axis=2)
        flatten_name = "{}_flatten".format(conf_name)
        net[flatten_name] = L.Flatten(net[softmax_name], axis=1)
        mbox_layers[1] = net[flatten_name]
    elif multibox_loss_param["conf_loss_type"] == P.MultiBoxLoss.LOGISTIC:
        sigmoid_name = "{}_sigmoid".format(conf_name)
        net[sigmoid_name] = L.Sigmoid(net[conf_name])
        mbox_layers[1] = net[sigmoid_name]

    net.detection_out = L.DetectionOutput(*mbox_layers,
                                          detection_output_param=det_out_param,
                                          include=dict(phase=caffe_pb2.Phase.Value('TEST')))
    net.detection_eval = L.DetectionEvaluate(net.detection_out, net.label,
                                             detection_evaluate_param=det_eval_param,
                                             include=dict(phase=caffe_pb2.Phase.Value('TEST')))

    with open(test_net_file, 'w') as f:
        print('name: "{}_test"'.format(model_name), file=f)
        print(net.to_proto(), file=f)
    shutil.copy(test_net_file, job_dir)

    # Create deploy net.
    # Remove the first and last layer from test net.
    deploy_net = net
    with open(deploy_net_file, 'w') as f:
        net_param = deploy_net.to_proto()
        # Remove the first (AnnotatedData) and last (DetectionEvaluate) layer from test net.
        del net_param.layer[0]
        del net_param.layer[-1]
        net_param.name = '{}_deploy'.format(model_name)
        net_param.input.extend(['data'])
        net_param.input_shape.extend([
            caffe_pb2.BlobShape(dim=[1, 3, resize_height, resize_width])])
        print(net_param, file=f)
    shutil.copy(deploy_net_file, job_dir)

    # Create solver.
    solver = caffe_pb2.SolverParameter(
        train_net=train_net_file,
        test_net=[test_net_file],
        snapshot_prefix=snapshot_prefix,
        **solver_param)

    with open(solver_file, 'w') as f:
        print(solver, file=f)
    shutil.copy(solver_file, job_dir)

    # Create job file.
    with open(job_file, 'w') as f:
        #f.write('cd {}\n'.format(caffe_root))
        f.write('{}/build/tools/caffe train \\\n'.format(caffe_root))
        f.write('--solver="{}" \\\n'.format(solver_file))
        f.write('--weights="{}" \\\n'.format(pretrain_model))
        if solver_param['solver_mode'] == P.Solver.GPU:
            f.write('--gpu {} 2>&1 | tee {}/{}_test{}.log\n'.format(gpus,
                                                                    job_dir, model_name, max_iter))
        else:
            f.write('2>&1 | tee {}/{}.log\n'.format(job_dir, model_name))

    # Copy the python script to job_dir.
    py_file = os.path.abspath(__file__)
    shutil.copy(py_file, job_dir)

    # Run the job.
    os.chmod(job_file, stat.S_IRWXU)
    if run_soon:
        subprocess.call(job_file, shell=True)


def parse_args():
    '''parse args'''
    parser = argparse.ArgumentParser()
    #parser.add_argument('--gpu_id', type=int, default=0, help='gpu id')
    parser.add_argument('--gen_dir', default=default_dataset_gen_dir)
    parser.add_argument('--image_resize', default=default_img_size, type=int)
    parser.add_argument('--labelmap_file', default=default_label_map)

    return parser.parse_args()


if __name__ == '__main__':
    main(parse_args())
