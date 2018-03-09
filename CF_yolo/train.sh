#!/usr/bin/env sh

CAFFE_ROOT="$HOME/CAFFE_SSD"
ROOT_DIR="/media/ps/AAA/CF_tools"


usage() { echo "Usage: $0 [-g <Gen path (VOC0712|Pedestrian gen)>]" 1>&2; exit 1; }

while getopts ":g:" o; do
    case "${o}" in
        g)
            gen_dir=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${gen_dir}" ]; then
    usage
fi


SOLVER=$ROOT_DIR/models/YOLO_$gen_dir/gnet_solver.prototxt
LOGFILE=$ROOT_DIR/logs/YOLO_$gen_dir/voc_log.log

$CAFFE_ROOT/build/tools/caffe train \
    --solver=$SOLVER --gpu=0 2>&1 | tee $LOGFILE
