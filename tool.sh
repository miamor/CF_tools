#!/bin/bash

# This example requires bash.

GTKDIALOG=gtkdialog
ROOT_DIR="$HOME/CF_tools"

export TMPDIR=/tmp/gtkdialog/examples/"`basename $0`"
mkdir -p "$TMPDIR"


funcmuiCreate() {
	echo '<variable>'$1'</variable>'
	if [ $2 = 1 ]; then echo '<label>"'"$3"'"</label>'; fi
	echo '<action>echo "'"$1 ($3) action for default signal triggered"'"</action>'
	if [ ${1:0:3} = "mnu" ]; then echo '</menu>'; else echo '</menuitem>'; fi
}

echo -n > "$TMPDIR"/inoutfile



funcbtnCreate() {
	echo '<button>
			<label>"'"$2"'"</label>
			<action>echo "'"$3"' '$1'"</action>
			<action function="'"$4"'">'$1'</action>
		</button>'
}

funcentCreate() {
	echo '<variable>'$1'</variable>
			<action>echo "'$1' action for default signal triggered"</action>
			<action signal="changed">echo "'$1' changed to $'$1'"</action>
			<action signal="activate">echo "'$1' Enter key-press detected"</action>
			<action signal="primary-icon-press">echo "'$1' primary icon press detected"</action>
			<action signal="primary-icon-release">echo "'$1' primary icon release detected"</action>
			<action signal="secondary-icon-press">echo "'$1' secondary icon press detected"</action>
			<action signal="secondary-icon-release">echo "'$1' secondary icon release detected"</action>
		</entry>'
	#if [ $2 = 1 ]; then echo '<vseparator></vseparator>'; fi
	#if [ $3 = 1 ]; then echo '</hbox><hseparator></hseparator><hbox>'; fi
}

train__log="/dev/pts/2"
test__log="/dev/pts/4"

funcSubmitForm() {
	#gpu_id=0
	# paste the script here~
	if [ $1 == "train_evaluate" ]
	then
		#funcLog train
		gen_dir=$gen_dir__train
		model=$model__train
		weight_file=$weight_file__train
		LABEL_FILE=$gen_dir__train/ssd/label_map.txt

		#img_size=${img_size__train##*x}
		img_size=$img_size__train

		#echo '<action>python $ROOT_DIR/CF_$model__train/${model__train}_pascal.py --gen_dir=$gen_dir --image_resize=$img_size__train --model_weights=$weight_file__train --labelmap_file=$LABEL_FILE 2>'"$train__log"'</action>'
		#echo '<action>python $ROOT_DIR/CF_$model__train/${model__train}_pascal.py --gen_dir=$gen_dir__train --image_resize=$img_size__train --model_weights=$weight_file__train --labelmap_file=$LABEL_FILE 2>&1</action>'
		echo '<action>echo ./run_tool.sh  -t $type  -g $gen_dir__train  -m $model__train  -s $img_size__train  -w $weight_file__train  2>&1</action>'
		echo '<action>./run_tool.sh  -t train  -g $gen_dir__train  -m $model__train  -s $img_size__train  -w $weight_file__train  2>&1</action>'
	
	elif [ $1 == "detect" ]
	then
		#gpu_id=$gpu_id__test
		gen_dir=$gen_dir__test
		model=$model__test
		weight_file=$weight_file__test
		LABEL_FILE=$gen_dir__test/ssd/label_map.txt

		img_size=$img_size__test

		#echo '<action>python $ROOT_DIR/CF_$model__test/${model__test}_pascal.py --gen_dir=$gen_dir__test --image_resize=$img_size__test --model_weights=$weight_file__test --labelmap_file=$LABEL_FILE 2>&1</action>'
		
		echo '<action>echo ./run_tool.sh  -t detect  -g $gen_dir__test  -m $model__test  -s $img_size__test  -w $weight_file__test  -i $img_file  2>&1</action>'
		echo '<action>./run_tool.sh  -t detect  -u $gpu_id  -g $gen_dir__test  -m $model__test  -s $img_size__test  -w $weight_file__test  -i $img_file  2>&1</action>'

	elif [ $1 == "prepare_data" ]
	then
		gen_dir=$gen_dir__prepare
		model=$model__prepare
		weight_file=$weight_file__prepare
		LABEL_FILE=$gen_dir__prepare/ssd/label_map.txt

		img_size=$img_size__prepare
		
		echo '<action>echo ./prepare_data.sh  -g $gen_dir__prepare  -m $model__prepare  -w $weight_file__prepare  2>&1</action>'
		echo '<action>./prepare_data.sh  -g $gen_dir__prepare  -m $model__prepare  -w $weight_file__prepare  2>&1</action>'
	fi

	# Execute commands
	#cho '<action>echo ./run_tool_.sh -w $weight_file -g $gen_dir -m $model -t train -s $img_size > '"$train__log"'</action>'
	#echo '<action>./run_tool_.sh -w $weight_file -g $gen_dir -m $model -t train -s $img_size > '"$train__log"'</action>'
	#echo '<action>echo hello $model</action>'
	#echo '<action>python $ROOT_DIR/CF_$model/${model}_pascal.py --gen_dir=$gen_dir --image_resize=$img_size --model_weights=$weight_file --labelmap_file=$LABEL_FILE 2>'"$train__log"'</action>'


	#echo 'funcSubmitForm '$1' '$2''
}

funcLog() {
	if [ $1 == "train_evaluate" ]
	then
		WELCOME="Hi! Tutu here"
		__tty=$tty
		#echo '<input>echo echo \$tty</input>
		#	<action>echo "log__train=$log__train"</action>'
	fi
}


for func in $(declare -F | cut -f3 -d' ')
do
	echo $func
    export -f $func
done


export -f funcSubmitForm


export MAIN_DIALOG='
<window title="Tool" resizable="true" width-request="400" border-width="0" scrollable="true">
	<vbox>
		<notebook labels="Train - Evaluate|Detect|Prepare datasets">			
			<vbox border-width="10" spacing="10">
					<hbox>
						<text>
							<label>Type:</label>
						</text>
						<comboboxentry  active="0">
							<variable>type</variable>
							<item>Train</item>
							<item>Evaluate</item>
						</comboboxentry>
					</hbox>

					<hbox>
						<text>
							<label>Model:</label>
						</text>
						<comboboxentry  active="0">
							<variable>model__train</variable>
							<item>ssd</item>
							<item>fssd</item>
							<item>yolo</item>
						</comboboxentry>
					</hbox>

					<hbox>
						<text>
							<label>Input size:</label>
						</text>
						<comboboxentry  active="0">
							<variable>img_size__train</variable>
							<item>300</item>
							<item>512</item>
							<item>448</item>
						</comboboxentry>
					</hbox>
					
					<hbox>
						<text>
							<label>Dataset generation dir:</label>
						</text>
						<entry fs-action="folder"
							fs-title="Select folder" 
							editable="false"
							block-function-signals="true">
						<output file>'"$TMPDIR"'/outputfile</output>
						
						'"`funcentCreate gen_dir__train 0 0`"'

						'"`funcbtnCreate gen_dir__train Select """Inserting into""" fileselect`"'
					</hbox>

					<hbox>
						<text>
							<label>Model weight (.caffemodel)</label>
						</text>
						<entry fs-action="file"
							fs-title="Select a file" 
							fs-filters="*.caffemodel"
							editable="false"
							block-function-signals="true">
						<output file>'"$TMPDIR"'/outputfile</output>
						
						'"`funcentCreate weight_file__train 0 0`"'
						
						'"`funcbtnCreate weight_file__train Select """Inserting into""" fileselect`"'
					</hbox>

					<hbox homogeneous="true">
						<button>
							<label>Execute</label>
							'"`funcSubmitForm train_evaluate`"'
						</button>
					</hbox>
			</vbox>


			<vbox border-width="10" spacing="10">
					<hbox>
						<text>
							<label>Model:</label>
						</text>
						<comboboxentry  active="0">
							<variable>model__test</variable>
							<item>ssd</item>
							<item>fssd</item>
							<item>yolo</item>
						</comboboxentry>
					</hbox>

					<hbox>
						<text>
							<label>Input size:</label>
						</text>
						<comboboxentry  active="0">
							<variable>img_size__test</variable>
							<item>300</item>
							<item>512</item>
							<item>448</item>
						</comboboxentry>
					</hbox>
					
					<hbox>
						<text>
							<label>Dataset generation dir name:</label>
						</text>
						<entry fs-action="folder"
							fs-title="Select folder" 
							editable="false"
							block-function-signals="true">
						<output file>'"$TMPDIR"'/outputfile</output>
						
						'"`funcentCreate gen_dir__test 0 0`"'

						'"`funcbtnCreate gen_dir__test Select """Inserting into""" fileselect`"'
					</hbox>

					<hbox>
						<text>
							<label>Model weight (.caffemodel)</label>
						</text>
						<entry fs-action="file"
							fs-title="Select a file" 
							fs-filters="*.caffemodel"
							editable="false"
							block-function-signals="true">
						<output file>'"$TMPDIR"'/outputfile</output>
						
						'"`funcentCreate weight_file__test 0 0`"'
						
						'"`funcbtnCreate weight_file__test Select """Inserting into""" fileselect`"'
					</hbox>

					<hbox>
						<text>
							<label>Test image </label>
						</text>
						<entry fs-action="file"
							fs-title="Select a file" 
							editable="false"
							block-function-signals="true">
						<output file>'"$TMPDIR"'/outputfile</output>
						
						'"`funcentCreate img_file 0 0`"'
						
						'"`funcbtnCreate img_file Select """Inserting into""" fileselect`"'
					</hbox>

					<hbox homogeneous="true">
						<button>
							<label>Execute</label>
							'"`funcSubmitForm detect`"'
						</button>
						<button cancel></button>
					</hbox>
			</vbox>

			<vbox border-width="10" spacing="10">
					<hbox>
						<text>
							<label>Model:</label>
						</text>
						<comboboxentry  active="0">
							<variable>model__prepare</variable>
							<item>ssd</item>
							<item>fssd</item>
							<item>yolo</item>
						</comboboxentry>
					</hbox>
					
					<hbox height="10" width="1000">
						<text>
							<label>Dataset directory:</label>
						</text>
						<entry fs-action="folder"
							fs-title="Select folder" 
							editable="false"
							block-function-signals="true">
						<output file>'"$TMPDIR"'/outputfile</output>
						
						'"`funcentCreate dataset_dir__prepare 0 0`"'

						'"`funcbtnCreate dataset_dir__prepare Select """Inserting into""" fileselect`"'
					</hbox>

					<hbox>
						<text>
							<label>Dataset generation dir:</label>
						</text>
						<entry fs-action="folder"
							fs-title="Select folder" 
							editable="false"
							block-function-signals="true">
						<output file>'"$TMPDIR"'/outputfile</output>
						
						'"`funcentCreate gen_dir__prepare 0 0`"'

						'"`funcbtnCreate gen_dir__prepare Select """Inserting into""" fileselect`"'
					</hbox>

					<hbox>
						<text>
							<label>Pretrained weight (.caffemodel)</label>
						</text>
						<entry fs-action="file"
							fs-title="Select a file" 
							fs-filters="*.caffemodel"
							editable="false"
							block-function-signals="true">
						<output file>'"$TMPDIR"'/outputfile</output>
						
						'"`funcentCreate weight_file__prepare 0 0`"'
						
						'"`funcbtnCreate weight_file__prepare Select """Inserting into""" fileselect`"'
					</hbox>

					<hbox homogeneous="true">
						<button>
							<label>Execute</label>
							'"`funcSubmitForm prepare_data`"'
						</button>
					</hbox>
			</vbox>
			
		</notebook>

	</vbox>
</window>
'

case $1 in
	-d | --dump) echo "$MAIN_DIALOG" ;;
	*) $GTKDIALOG --program=MAIN_DIALOG ;;
esac
