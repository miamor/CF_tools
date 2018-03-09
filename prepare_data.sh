#!/bin/bash

CAFFE_ROOT="$HOME/CAFFE_SSD"
ROOT_DIR="$HOME/CF_tools"
#ROOT_DIR="./"
#dataset_dir="VOCdevkit" # or Pedestrian
#model="ssd" # or yolo

usage() { echo "Usage: $0 [-g <Gen path (VOC0712|Pedestrian gen)>] [-d <Dataset path (/../VOCdevkit)>] [-m <Model (ssd|fssd|yolo)>]" 1>&2; exit 1; }

while getopts ":g:d:m:" o; do
    case "${o}" in
        g)
            gen_dir=${OPTARG}
            ;;
        d)
            dataset_dir=${OPTARG}
            ;;
        m)
            model=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${gen_dir}" ] || [ -z "${dataset_dir}" ] || [ -z "${model}" ]; then
    usage
fi

#data_ROOT_DIR="data/$dataset_dir"
data_ROOT_DIR=$dataset_dir
bash_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"


if [ $model == "fssd" ]
then
  model="ssd"
fi



# create neccessary files

#dst_path="data/$gen_dir/$model"   # data/VOC0712/ssd
dst_path="$gen_dir/$model"
gen_dir_name=${gen_dir##*/}
echo $gen_dir_name

for dataset in trainval test
do
  if [ ! -d "$dst_path" ]; then
	mkdir -p "$dst_path"
  fi
  
  dst_file=$dst_path/$dataset.txt   # data/VOC0712/ssd/trainval.txt
  if [ -f $dst_file ]
  then
    rm -f $dst_file
  fi

  for data_name in "$data_ROOT_DIR"/*
  do
    name=$(basename "$data_name")
    if [[ $dataset == "test" && $name == "VOC2012" ]]
    then
      continue
    fi
    echo "Create list for $name $dataset..."
    data_folder=$data_ROOT_DIR$name

    for img_file in "$data_ROOT_DIR/$name/JPEGImages"/*
    do
      filename=$(basename "$img_file")
      extension="${filename##*.}"
      filename="${filename%.*}"
      label_file="$data_ROOT_DIR/$name/Annotations/$filename.xml"
      echo "$img_file $label_file" >> $dst_file
    done
  done

  # Generate image name and size infomation.
  if [ $dataset == "test" ]
  then
    $CAFFE_ROOT/build/tools/get_image_size $ROOT_DIR $dst_file $dst_path/$dataset"_name_size.txt"
  fi

  # Shuffle trainval file.
  if [ $dataset == "trainval" ]
  then
    rand_file=$dst_file.random
    cat $dst_file | perl -MList::Util=shuffle -e 'print shuffle(<STDIN>);' > $rand_file
    mv $rand_file $dst_file
  fi
done



# create lmdb
#LABEL_FILE=$ROOT_DIR/data/$gen_dir/{$model}/label_map.txt
LABEL_FILE=$gen_dir/{$model}/label_map.txt

if [ $model == "ssd" ]
then
    redo=1
    anno_type="detection"
    db="lmdb"
    min_dim=0
    max_dim=0
    width=0
    height=0

    extra_cmd="--encode-type=jpg --encoded"
    if [ $redo ]
    then
    extra_cmd="$extra_cmd --redo"
    fi
    for subset in test trainval
    do
    # Not really sure what the exampledir is needed for
    python $CAFFE_ROOT/scripts/create_annoset.py --anno-type=$anno_type --label-map-file=$LABEL_FILE --min-dim=$min_dim --max-dim=$max_dim --resize-width=$width --resize-height=$height --check-label $extra_cmd $ROOT_DIR $gen_dir/ssd/$subset.txt $ROOT_DIR/$db/$gen_dir_name"_"$subset"_"$db examples/$gen_dir_name
    #python $CAFFE_ROOT/scripts/create_annoset.py --anno-type=$anno_type --label-map-file=$LABEL_FILE --min-dim=$min_dim --max-dim=$max_dim --resize-width=$width --resize-height=$height --check-label $extra_cmd $ROOT_DIR $ROOT_DIR/data/$gen_dir/ssd/$subset.txt $ROOT_DIR/$db/$gen_dir"_"$subset"_"$db
    done
fi


if [ $model == "yolo" ]
then
    # trainval
    LIST_FILE_TRAIN=$gen_dir/yolo/trainval.txt
    TRAIN_NAME=${gen_dir_name}_yolo_trainval
    LMDB_DIR_TRAIN=$ROOT_DIR/lmdb/${TRAIN_NAME}_lmdb
    SHUFFLE_TRAIN=true

    # test
    LIST_FILE_TEST=$gen_dir/yolo/test.txt
    TEST_NAME=${gen_dir_name}_yolo_test
    LMDB_DIR_TEST=$ROOT_DIR/lmdb/${TEST_NAME}_lmdb
    SHUFFLE_TEST=false

    RESIZE_W=448
    RESIZE_H=448


    $CAFFE_ROOT/build/tools/convert_box_data --resize_width=$RESIZE_W --resize_height=$RESIZE_H \
    --label_file=$LABEL_FILE $ROOT_DIR/ $LIST_FILE_TRAIN $LMDB_DIR_TRAIN --encoded=true --encode_type=jpg --shuffle=$SHUFFLE_TRAIN

    $CAFFE_ROOT/build/tools/convert_box_data --resize_width=$RESIZE_W --resize_height=$RESIZE_H \
    --label_file=$LABEL_FILE $ROOT_DIR/ $LIST_FILE_TEST $LMDB_DIR_TEST --encoded=true --encode_type=jpg --shuffle=$SHUFFLE_TEST


    $CAFFE_ROOT/build/tools/compute_image_mean $LMDB_DIR_TRAIN lmdb/${TRAIN_NAME}.binaryproto
    $CAFFE_ROOT/build/tools/compute_image_mean $LMDB_DIR_TEST  lmdb/${TEST_NAME}.binaryproto

fi
