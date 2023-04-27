CHECKPOINT=adgen-chatglm-6b-pt-128-2e-2
STEP=1200
PRE_SEQ_LEN=128

CUDA_VISIBLE_DEVICES=0 python3 ./service/main.py \
     --model_name_or_path THUDM/chatglm-6b \
     --ptuning_checkpoint /root/autodl-tmp/zechen_work/law_for_chat/ptuning/output/$CHECKPOINT/checkpoint-$STEP \
     --cache_dir /root/autodl-tmp/zechen_work/law_for_chat/ptuning/cache_dir  \
     --pre_seq_len $PRE_SEQ_LEN
