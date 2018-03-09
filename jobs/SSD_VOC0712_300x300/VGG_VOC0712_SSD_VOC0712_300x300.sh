/home/tunguyen/CAFFE/build/tools/caffe train \
--solver="/home/tunguyen/CF_tools/models/SSD_VOC0712_300x300/solver.prototxt" \
--snapshot="/home/tunguyen/CF_tools/snapshot_models/SSD_VOC0712_300x300/VGG_VOC0712_SSD_VOC0712_300x300_iter_23.solverstate" \
--gpu 0 2>&1 | tee /home/tunguyen/CF_tools/jobs/SSD_VOC0712_300x300/VGG_VOC0712_SSD_VOC0712_300x300_20180309091401.log
