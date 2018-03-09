/home/ps/CAFFE_SSD/build/tools/caffe train \
--solver="/media/ps/AAA/CF_tools/models/FSSD_VOC0712_300x300/solver.prototxt" \
--weights="/media/ps/AAA/CF_tools/snapshot_models/FSSD_VOC0712_300x300/VGG_VOC0712_FSSD_VOC0712_300x300_iter_11.caffemodel" \
--gpu 0 2>&1 | tee /media/ps/AAA/CF_tools/jobs/FSSD_VOC0712_300x300/VGG_VOC0712_FSSD_VOC0712_300x300_test11.log
