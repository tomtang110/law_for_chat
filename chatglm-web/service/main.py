import os
import uvicorn
import json
import traceback
import uuid
import argparse

from os.path import abspath, dirname
from loguru import logger
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from message_store import MessageStore
from transformers import AutoModel, AutoTokenizer, AutoConfig
from errors import Errors
# import knowledge
import torch
import gen_data

log_folder = os.path.join(abspath(dirname(__file__)), "log")
logger.add(os.path.join(log_folder, "{time}.log"), level="INFO")

DEFAULT_DB_SIZE = 100000

massage_store = MessageStore(
    db_path="message_store.json",
    table_name="chatgpt",
    max_size=DEFAULT_DB_SIZE
)
# Timeout for FastAPI
# service_timeout = None

app = FastAPI()

stream_response_headers = {
    "Content-Type": "application/octet-stream",
    "Cache-Control": "no-cache",
}


@app.post("/config")
async def config():
  return JSONResponse(content=dict(message=None, status="Success", data=dict()))


async def process(
    prompt, options, params, message_store, is_knowledge, history=None
):
  """
    发文字消息
    """
  # 不能是空消息
  if not prompt:
    logger.error("Prompt is empty.")
    yield Errors.PROMPT_IS_EMPTY.value
    return

  try:
    chat = {"role": "user", "content": prompt}

    # 组合历史消息
    if options:
      parent_message_id = options.get("parentMessageId")
      messages = message_store.get_from_key(parent_message_id)
      if messages:
        messages.append(chat)
      else:
        messages = []
    else:
      parent_message_id = None
      messages = [chat]

    # 记忆
    messages = messages[-params['memory_count']:]

    history_formatted = []
    if options is not None:
      history_formatted = []
      tmp = []
      for i, old_chat in enumerate(messages):
        if len(tmp) == 0 and old_chat['role'] == "user":
          tmp.append(old_chat['content'])
        elif old_chat['role'] == "AI":
          tmp.append(old_chat['content'])
          history_formatted.append(tuple(tmp))
          tmp = []
        else:
          continue

    uid = "chatglm" + uuid.uuid4().hex
    footer = ''
    # if is_knowledge:
    #     response_d = knowledge.find_whoosh(prompt)
    #     output_sources = [i['title'] for i in response_d]
    #     results ='\n---\n'.join([i['content'] for i in response_d])
    #     prompt=  f'system:基于以下内容，用中文简洁和专业回答用户的问题。\n\n'+results+'\nuser:'+prompt
    #     footer=  "\n参考：\n"+('\n').join(output_sources)+''
    # yield footer
    for response, history in model.stream_chat(
        tokenizer,
        prompt,
        history_formatted,
        max_length=params['max_length'],
        top_p=params['top_p'],
        temperature=params['temperature']
    ):
      message = json.dumps(
          dict(
              role="AI",
              id=uid,
              parentMessageId=parent_message_id,
              text=response + footer,
          )
      )
      yield "data: " + message

  except:
    err = traceback.format_exc()
    logger.error(err)
    yield Errors.SOMETHING_WRONG.value
    return

  try:
    # save to cache
    chat = {"role": "AI", "content": response}
    messages.append(chat)

    parent_message_id = uid
    message_store.set(parent_message_id, messages)
  except:
    err = traceback.format_exc()
    logger.error(err)


@app.post("/chat-process")
async def chat_process(request_data: dict):
  prompt = request_data['prompt']
  max_length = request_data['max_length']
  top_p = request_data['top_p']
  temperature = request_data['temperature']
  options = request_data['options']
  if request_data['memory'] == 1:
    memory_count = 5
  elif request_data['memory'] == 50:
    memory_count = 20
  else:
    memory_count = 999

  if 1 == request_data["top_p"]:
    top_p = 0.2
  elif 50 == request_data["top_p"]:
    top_p = 0.5
  else:
    top_p = 0.9
  if temperature is None:
    temperature = 0.9
  if top_p is None:
    top_p = 0.7
  is_knowledge = request_data['is_knowledge']
  params = {
      "max_length": max_length,
      "top_p": top_p,
      "temperature": temperature,
      "memory_count": memory_count
  }
  answer_text = process(prompt, options, params, massage_store, is_knowledge)
  return StreamingResponse(
      content=answer_text,
      headers=stream_response_headers,
      media_type="text/event-stream"
  )


def initalize_model(model_args):
  # initialize model
  # Load pretrained model and tokenizer
  config = AutoConfig.from_pretrained(
      model_args.model_name_or_path,
      trust_remote_code=True,
      cache_dir=model_args.cache_dir
  )
  config.pre_seq_len = model_args.pre_seq_len
  config.prefix_projection = False
  tokenizer = AutoTokenizer.from_pretrained(
      model_args.model_name_or_path,
      config=config,
      trust_remote_code=True,
      cache_dir=model_args.cache_dir
  )
  model = AutoModel.from_pretrained(
      model_args.model_name_or_path,
      config=config,
      trust_remote_code=True,
      cache_dir=model_args.cache_dir
  ).half().cuda()
  model = model.eval()
  prefix_state_dict = torch.load(
      os.path.join(model_args.ptuning_checkpoint, "pytorch_model.bin")
  )
  new_prefix_state_dict = {}
  for k, v in prefix_state_dict.items():
    if k.startswith("transformer.prefix_encoder."):
      new_prefix_state_dict[k[len("transformer.prefix_encoder."):]] = v
  model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)
  return model, tokenizer


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
      description='Simple API server for ChatGLM-6B'
  )
  parser.add_argument(
      '--device', '-d', help='使用设备，cpu或cuda:0等', default='cuda:0'
  )
  parser.add_argument('--quantize', '-q', help='量化等级。可选值：16，8，4', default=16)
  parser.add_argument(
      '--model_name_or_path', '-m', help='模型名或地址', default="THUDM/chatglm-6b"
  )
  parser.add_argument('--cache_dir', '-c', help='缓存', default="./cache_dir")
  parser.add_argument(
      '--pre_seq_len', '-s', type=int, help='pre seq len', default="128"
  )
  parser.add_argument(
      '--ptuning_checkpoint',
      '-p',
      help='ptuning checkpoint',
      default="./output"
  )
  parser.add_argument(
      '--host', '-H', type=str, help='监听Host', default='0.0.0.0'
  )
  parser.add_argument('--port', '-P', type=int, help='监听端口号', default=3002)
  args = parser.parse_args()
  model, tokenizer = initalize_model(args)
  uvicorn.run(app, host=args.host, port=args.port)
