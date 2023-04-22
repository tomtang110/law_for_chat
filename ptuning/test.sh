CHECKPOINT=adgen-chatglm-6b-pt-128-2e-2
STEP=1200
PRE_SEQ_LEN=128

CUDA_VISIBLE_DEVICES=0 python3 demo.py \
     --model_name_or_path THUDM/chatglm-6b \
     --ptuning_checkpoint ./output/$CHECKPOINT/checkpoint-$STEP \
     --cache_dir ./cache_dir  \
     --pre_seq_len $PRE_SEQ_LEN \