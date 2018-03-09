#!/bin/bash

CAFFE_ROOT="$HOME/CAFFE_SSD"
ROOT_DIR="$HOME/CF_tools"
#ROOT_DIR="./"
#dataset_dir="VOCdevkit" # or Pedestrian
#model="ssd" # or yolo

usage() { echo "Usage: $0 [-t <Train|Test|Evaluate] [-g <Gen path (VOC0712|PedGen)>] [-m <Model (ssd|fssd|yolo)>] [-w <weight_file>] [-s <img_size>] [-u <gpu_id>] [-i <image file>] " 1>&2; exit 1; }


while getopts ":t:g:m:w:s:u:i:" o; do
    case "${o}" in
        g)
            gen_dir=${OPTARG}
            ;;
        t)
            type=${OPTARG}
            ;;
        m)
            model=${OPTARG}
            ;;
        w)
            weight_file=${OPTARG}
            ;;
        s)
            img_size=${OPTARG}
            ;;
        u)
            gpu_id=${OPTARG}
            ;;
        i)
            img_file=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))


gen_dir_name=${gen_dir##*/}


if [ "$model" == "ssd" ] || [ "$model" == "fssd" ]
then
    LABEL_FILE=$gen_dir/ssd/label_map.txt
fi

if [ "$model" == "yolo" ]
then
    LABEL_FILE=$gen_dir/yolo/label_map.txt
fi


if [ "$type" == "detect" ]
then
    if [ "$model" == "ssd" ] || [ "$model" == "fssd" ]
    then
        python $ROOT_DIR/CF_$model/${model}_detect.py --gpu_id=$gpu_id --labelmap_file=$LABEL_FILE --image_resize=$img_size --model_weights=$weight_file --image_file=$img_file 2>&1
    fi

fi

if [ "$type" == "train" ]
then
    if [ "$model" == "ssd" ] || [ "$model" == "fssd" ]
    then
        python $ROOT_DIR/CF_$model/${model}_pascal.py --gen_dir=$gen_dir_name --image_resize=$img_size --model_weights=$weight_file --labelmap_file=$LABEL_FILE 2>&1
    fi

fi

if [ "$type" == "evaluate" ]
then
    if [ "$model" == "ssd" ] || [ "$model" == "fssd" ]
    then
        python $ROOT_DIR/CF_$model/score_${model}_pascal.py --gen_dir=$gen_dir_name --image_resize=$img_size --model_weights=$weight_file --labelmap_file=$LABEL_FILE 2>&1
    fi

fi

