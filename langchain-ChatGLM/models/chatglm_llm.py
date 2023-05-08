import json
import os
from langchain.llms.base import LLM
from typing import Optional, List
from langchain.llms.utils import enforce_stop_tokens
from transformers import AutoTokenizer, AutoModel, AutoConfig
import torch
from configs.model_config import LLM_DEVICE
from langchain.callbacks.base import BaseCallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from typing import Dict, Optional

DEVICE = LLM_DEVICE
DEVICE_ID = "0" if torch.cuda.is_available() else None
CUDA_DEVICE = f"{DEVICE}:{DEVICE_ID}" if DEVICE_ID else DEVICE


def torch_gc():
    if torch.cuda.is_available():
        with torch.cuda.device(CUDA_DEVICE):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()


def auto_configure_device_map(num_gpus: int) -> Dict[str, int]:
    # transformer.word_embeddings 占用1层
    # transformer.final_layernorm 和 lm_head 占用1层
    # transformer.layers 占用 28 层
    # 总共30层分配到num_gpus张卡上
    num_trans_layers = 28
    per_gpu_layers = 30 / num_gpus

    # bugfix: 在linux中调用torch.embedding传入的weight,input不在同一device上,导致RuntimeError
    # windows下 model.device 会被设置成 transformer.word_embeddings.device
    # linux下 model.device 会被设置成 lm_head.device
    # 在调用chat或者stream_chat时,input_ids会被放到model.device上
    # 如果transformer.word_embeddings.device和model.device不同,则会导致RuntimeError
    # 因此这里将transformer.word_embeddings,transformer.final_layernorm,lm_head都放到第一张卡上
    device_map = {'transformer.word_embeddings': 0,
                  'transformer.final_layernorm': 0, 'lm_head': 0}

    used = 2
    gpu_target = 0
    for i in range(num_trans_layers):
        if used >= per_gpu_layers:
            gpu_target += 1
            used = 0
        assert gpu_target < num_gpus
        device_map[f'transformer.layers.{i}'] = gpu_target
        used += 1

    return device_map


class ChatGLM(LLM):
    max_token: int = 10000
    temperature: float = 0.01
    top_p = 0.9
    # history = []
    tokenizer: object = None
    model: object = None
    history_len: int = 10
    streaming: bool = True
    callback_manager = BaseCallbackManager([StreamingStdOutCallbackHandler()])

    def __init__(self):
        super().__init__()

    @property
    def _llm_type(self) -> str:
        return "ChatGLM"

    def _call(self,
              prompt: str,
              history: List[List[str]] = [],
              stop: Optional[List[str]] = None) -> str:
        if self.streaming:
            for inum, (stream_resp, _) in enumerate(self.model.stream_chat(
                    self.tokenizer,
                    prompt,
                    history=history[-self.history_len:-1] if self.history_len > 0 else [],
                    max_length=self.max_token,
                    temperature=self.temperature,
            )):
                if inum == 0:
                    history += [[prompt, stream_resp]]
                else:
                    history[-1] = [prompt, stream_resp]
                yield stream_resp, history

        else:
            response, _ = self.model.chat(
                self.tokenizer,
                prompt,
                history=history[-self.history_len:] if self.history_len > 0 else [],
                max_length=self.max_token,
                temperature=self.temperature,
            )
            torch_gc()
            if stop is not None:
                response = enforce_stop_tokens(response, stop)
            history = history + [[None, response]]
            return response, history

    # def chat(self,
    #          prompt: str) -> str:
    #     response, _ = self.model.chat(
    #         self.tokenizer,
    #         prompt,
    #         history=self.history[-self.history_len:] if self.history_len > 0 else [],
    #         max_length=self.max_token,
    #         temperature=self.temperature,
    #     )
    #     torch_gc()
    #     self.history = self.history + [[None, response]]
    #     return response

    def initalize_model(self, model_args):
        # initialize model
        # Load pretrained model and tokenizer
        config = AutoConfig.from_pretrained(
            model_args.model_name_or_path,
            trust_remote_code=True,
            cache_dir=model_args.cache_dir
            )
        config.pre_seq_len = model_args.pre_seq_len
        config.prefix_projection = model_args.prefix_projection
        print("autoCOnfig: ", model_args.prefix_projection)
        tokenizer = AutoTokenizer.from_pretrained(model_args.model_name_or_path, config=config, trust_remote_code=True, cache_dir=model_args.cache_dir)
        model = AutoModel.from_pretrained(model_args.model_name_or_path, config=config, trust_remote_code=True, cache_dir=model_args.cache_dir).half().cuda()
        model = model.eval()
        prefix_state_dict = torch.load(os.path.join(model_args.ptuning_checkpoint, "pytorch_model.bin"))
        new_prefix_state_dict = {}
        for k, v in prefix_state_dict.items():
            if k.startswith("transformer.prefix_encoder."):
                new_prefix_state_dict[k[len("transformer.prefix_encoder."):]] = v
            model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)
        return model, tokenizer

    def load_model(self,
                   model_name_or_path: str = "THUDM/chatglm-6b",
                   llm_device=LLM_DEVICE,
                   use_ptuning_v2=False,
                   model_config=None,
                   device_map: Optional[Dict[str, int]] = None,
                   **kwargs):
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            trust_remote_code=True
        )

        if model_config != None:
            model, tokenizer = self.initalize_model(model_config)
            self.model = model
            self.tokenizer = tokenizer
        else:
            print("模型配置为空。")

        # model_config = AutoConfig.from_pretrained(model_name_or_path, trust_remote_code=True)

        # if use_ptuning_v2:
        #     try:
        #         prefix_encoder_file = open('ptuning-v2/config.json', 'r')
        #         prefix_encoder_config = json.loads(prefix_encoder_file.read())
        #         prefix_encoder_file.close()
        #         model_config.pre_seq_len = prefix_encoder_config['pre_seq_len']
        #         model_config.prefix_projection = prefix_encoder_config['prefix_projection']
        #     except Exception as e:
        #         print(e)
        #         print("加载PrefixEncoder config.json失败")

        # if torch.cuda.is_available() and llm_device.lower().startswith("cuda"):
        #     # 根据当前设备GPU数量决定是否进行多卡部署
        #     num_gpus = torch.cuda.device_count()
        #     if num_gpus < 2 and device_map is None:
        #         self.model = (
        #             AutoModel.from_pretrained(
        #                 model_name_or_path,
        #                 config=model_config,
        #                 trust_remote_code=True,
        #                 **kwargs)
        #             .half()
        #             .cuda()
        #         )
        #     else:
        #         from accelerate import dispatch_model

        #         model = (
        #             AutoModel.from_pretrained(
        #                 model_name_or_path,
        #                 trust_remote_code=True,
        #                 config=model_config,
        #                 **kwargs)
        #             .half())
        #         # 可传入device_map自定义每张卡的部署情况
        #         if device_map is None:
        #             device_map = auto_configure_device_map(num_gpus)

        #         self.model = dispatch_model(model, device_map=device_map)
        # else:
        #     self.model = (
        #         AutoModel.from_pretrained(
        #             model_name_or_path,
        #             config=model_config,
        #             trust_remote_code=True,
        #             **kwargs)
        #         .float()
        #         .to(llm_device)
        #     )

        # if use_ptuning_v2:
        #     try:
        #         prefix_state_dict = torch.load('ptuning-v2/pytorch_model.bin')
        #         new_prefix_state_dict = {}
        #         for k, v in prefix_state_dict.items():
        #             if k.startswith("transformer.prefix_encoder."):
        #                 new_prefix_state_dict[k[len("transformer.prefix_encoder."):]] = v
        #         self.model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)
        #         self.model.transformer.prefix_encoder.float()
        #     except Exception as e:
        #         print(e)
        #         print("加载PrefixEncoder模型参数失败")

        # self.model = self.model.eval()
