from flask import Flask, request
import json
import sys
import os

cwd = os.getcwd()
sys.path.append(os.path.join(cwd, 'trigger_code/dnn_pytorch/'))
sys.path.append(os.path.join(cwd, 'cnn_code/'))

# import the event extractor
import output_formatter_new_v5_singlecs_m18
import combine_ment_arg_new
import cnn_input_dryrun
import ltf_to_bio
import clean_up
import cnn_tag
import tag

# default paths and variables
#Please change the following to suit docker needs: ltf_folder_path, input_rsd_folder_path, input_edl_bio_file_path, entity_cs_file_path

ltf_folder_path = os.path.join(cwd, 'data/source/ru_all')
out_folder_path = os.path.join(cwd, 'intermediate_files')

model_file_path = os.path.join(cwd, 'trigger_code/dnn_pytorch/best_model.pth.tar')
input_file_path = os.path.join(cwd, 'intermediate_files/ru_all.bio')
output_file_path_1 = os.path.join(cwd, 'intermediate_files/ru_all_triggers_offset.bio')
batch_size = 50
gpu = 0

input_trigger_offset_file_path = os.path.join(cwd, 'intermediate_files/ru_all_triggers_offset.bio')
input_edl_bio_file_path = os.path.join(cwd, 'data/source/edl_results/ru.nam+nom.tagged.bio')
output_file_path_2 = os.path.join(cwd, 'intermediate_files/ru_all_merged.bio')

input_rsd_folder_path = os.path.join(cwd, 'data/source/ru_all_rsd')
input_merged_bio_file_path = os.path.join(cwd, 'intermediate_files/ru_all_merged.bio')

model_folder_path = os.path.join(cwd, 'cnn_code/runs/ru_1535939310/checkpoints/')
out_file_path = os.path.join(cwd, 'intermediate_files/ru_all.tsv')

rsd_folder_path = os.path.join(cwd, 'data/source/ru_all_rsd/')
entity_cs_file_path = os.path.join(cwd, 'data/source/edl_results/ru.merged.cs')
cs_file_path = os.path.join(cwd, 'results/ru_all.cs')
trig_offset_file_path = os.path.join(cwd, 'intermediate_files/ru_all_triggers_offset.bio')
cnn_out_file_path = os.path.join(cwd, 'intermediate_files/ru_all.tsv')

app = Flask(__name__)

# flask main framework
@app.route('/ru_event')
def ru_event():

    # STEP 1 clean up first
    clean_up.runner()

    # STEP 2 convert LTF to BIO format for trigger extraction
    ## INPUT:
    ### ltf_folder_path: input folder path containing LTF files, 

    ## OUTPUT:
    ### out_folder_path: the folder path to hold the created BIO format files.
    ltf_to_bio.runner(ltf_folder_path, out_folder_path)

    # STEP 3 run trigger extraction
    ## INPUT:
    ### model_file_path: path to stored model for trigger extraction, 
    ### input_file_path: path to ru_all.bio created by Step 2, 
    ### batch size: integer, 
    ### gpu: default is 0, set 1 to use gpu.

    ## OUTPUT:
    ### output_file_path_1: path to ru_all_triggers_offset.bio which will hold the extracted triggers and offsets,
    tag.runner(model_file_path, input_file_path, output_file_path_1, batch_size, gpu)

    # STEP 4 before argument extraction, we need to merge our trigger extraction results and entity extraction results, based on the correct offsets
    ## INPUT:
    ### input_trigger_offset_file_path: produced by Step 3 above, 
    ### input_edl_bio_file_path: is the BIO formated entity extraction results from Boliang's system

    ## OUTPUT:
    ### output_file_path_2: path to ru_all_merged.bio which will hold a single BIO file with trigger and entity results combined
    combine_ment_arg_new.runner(input_trigger_offset_file_path, input_edl_bio_file_path, output_file_path_2)

    # STEP 5 create the input for the CNN model for argument extraction
    ## INPUT:
    ### input_rsd_folder_path: folder containing the rsd files
    ### input_merged_bio_file_path: the output_file_path_2 from Step 4

    ## OUTPUT: is resovled by default to './intermediate_files/cnn_in/'
    cnn_input_dryrun.runner(input_rsd_folder_path, input_merged_bio_file_path)

    # STEP 6 run the argument extraction model
    ## INPUT:
    ### model_folder_path: the folder containing the pre-trained model for argument extraction
    ### This method expects to find results in './intermediate_files/cnn_in/' generated by Step 5. The directory structure of /cnn_in is very important and must not be modified.

    ## OUTPUT
    ### out_file_path: the path to the output tsv file containing the results
    cnn_tag.runner(model_folder_path, out_file_path)

    # STEP 7 apply post processing rules and convert to CS format
    ## INPUT:
    ### rsd_folder_path: the path to the folder containing rsd files
    ### entity_cs_file_path: Xiaoman's EDL resulst CS file, used to get entity IDs for arguments.
    ### trig_offset_file_path: ru_all_triggers_offset.bio is output_file+path_1 from Step 3
    ### cnn_out_file_path: the tsv output file from Step 6

    ## OUTPUT:
    ### cs_file_path: The final result ru_all.cs in cold start format, placed in /results/ru_all.cs
    output_formatter_new_v5_singlecs_m18.runner(rsd_folder_path, entity_cs_file_path, cs_file_path, trig_offset_file_path, cnn_out_file_path)
    message = 'Russian Event Extraction complete. Results are in: ' + cs_file_path

    return message
    

# app.run(debug=True)
app.run(host='0.0.0.0', port=4242)