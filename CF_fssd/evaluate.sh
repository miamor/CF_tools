CAFFE_ROOT="$HOME/CAFFE_SSD"
ROOT_DIR="/media/ps/AAA/CF_tools"
#ROOT_DIR="./"

#bash_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

gen_dir="VOC0712"
img_size=300

while true; do
  case "$1" in
    -g | --gen-path )       gen_dir=$2;     shift ;;
    -s | --image-size )     img_size="$2";  shift; shift ;;
    -- ) shift; break ;;
    * ) break ;;
  esac
done


#SOLVER=$ROOT_DIR/models/SSD_$gen_dir/gnet_solver.prototxt
LOGFILE=$ROOT_DIR/logs/SSD_$gen_dir.log
LABEL_FILE=$ROOT_DIR/data/$gen_dir/ssd/label_map.txt

#python $ROOT_DIR/CF_ssd/ssd_pascal.py --gen_dir=$gen_dir --image_resize=$img_size 2>&1 | tee $LOGFILE
python $ROOT_DIR/CF_fssd/score_fssd_pascal.py --gen_dir=$gen_dir --image_resize=$img_size --labelmap_file=$LABEL_FILE 2>&1