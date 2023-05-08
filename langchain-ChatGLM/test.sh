PRE_SEQ_LEN=128
LR=2e-2
VER=2
CHECKPOINT=adgen-chatglm-6b-pt-128-2e-2-all
STEP=2400

CUDA_VISIBLE_DEVICES=0 python3 cli_demo.py \
     --model_name_or_path THUDM/chatglm-6b \
    --ptuning_checkpoint /root/autodl-tmp/zechen_work/law_for_chat/ptuning/output/$CHECKPOINT/checkpoint-$STEP \
     --cache_dir /root/autodl-tmp/zechen_work/law_for_chat/ptuning/cache_dir  \
     --pre_seq_len $PRE_SEQ_LEN