# CF_tools
Running caffe with SSD, FSSD, YOLO implemented    
Install caffe and its python module [here](https://github.com/miamor/caffe)

## Simple run
`./tool.sh`


## Get to more details
### Prepare data before train:
```
./prepare_data.sh \
	-g <dataset_gen_dir> \
	-d <dataset dir> \
	-m <model>
```

### Run tool
```
./run_tool.sh \
	-t <train|detect|evaluate> \
	-g <Generation path> \
	-m <Model (ssd|fssd|yolo)> \
	-w <weight_file> \
	-s <img_size> \
	-u <gpu_id>
```

## Train with your own dataset
