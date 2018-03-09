CAFFE_ROOT="$HOME/CAFFE_SSD"
ROOT_DIR="/media/ps/AAA/CF_tools"
#ROOT_DIR="./"

#bash_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

gpu_id=0
gen_dir="VOC0712"
weight_file="$ROOT_DIR/snapshot_models/SSD_300x300/VGG_VOC0712_SSD_300x300_iter_120000.caffemodel"
img_size=300
img_file="images/fish-bike.jpg"

while true; do
  case "$1" in
    -u | --gpu )            gpu_id=0;       shift ;;
    -g | --gen-path )       gen_dir=$2;     shift ;;
    -w | --weight )         weight_file=$2; shift ;;
    -i | --img )            img_file=$2;    shift ;;
    -s | --image-size )     img_size="$2";  shift; shift ;;
    -- ) shift; break ;;
    * ) break ;;
  esac
done


LABEL_FILE=$ROOT_DIR/data/$gen_dir/ssd/label_map.txt
#model_file=$ROOT_DIR/models/$gen_dir/ssd/deploy.prototxt

#python $ROOT_DIR/CF_ssd/ssd_detect.py --gpu_id=$gpu_id --labelmap_file=$LABEL_FILE --image_resize=$img_size --model_weights=$weight_file 2>&1 | tee $LOGFILE
python $ROOT_DIR/CF_ssd/ssd_detect.py --gpu_id=$gpu_id --labelmap_file=$LABEL_FILE --image_resize=$img_size --model_weights=$weight_file --image_file=$img_file 2>&1
