cd /media/ps/AAA/CF_tools
./build/tools/caffe train \
--solver="models/VGGNet/VOC0712/SSD_300x300_orig/solver.prototxt" \
--weights="models/VGGNet/VGG_ILSVRC_16_layers_fc_reduced.caffemodel" \
--gpu 0,1,2,3 2>&1 | tee jobs/VGGNet/VOC0712/SSD_300x300_orig/VGG_VOC0712_SSD_300x300_orig.log
