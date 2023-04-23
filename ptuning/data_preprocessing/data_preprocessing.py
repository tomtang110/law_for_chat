import argparse
import json
from tqdm import tqdm


class JsonPreprocessor:

  def __init__(self, data_path, save_path):
    self.data_path = data_path
    self.save_path = save_path

  @staticmethod
  def instruct_format_example(example, is_list) -> list:
    if is_list:
      features = []
      for ex in example:
        context = f"Instruction: {ex['instruction']}\n"
        if ex.get("input"):
          context += f"Input: {ex['input']}\n"
        context += "Answer: "
        target = ex["output"]
        features.append({"context": context, "target": target})

    else:
      context = f"Instruction: {example['instruction']}\n"
      if example.get("input"):
        context += f"Input: {example['input']}\n"
      context += "Answer: "
      target = example["output"]
    return [{"context": context, "target": target}]

  def process(self, is_list=False):
    with open(self.data_path, encoding='utf-8') as f:
      examples = f.read()

    parsed_json = json.loads(examples)

    features = []
    for example in tqdm(parsed_json, desc='Processing'):
      feature = self.instruct_format_example(example, is_list)
      features.extend(feature)

    with open(self.save_path, 'w', encoding='utf-8') as p:
      p.write(json.dumps(features, ensure_ascii=False))


if __name__ == "__main__":
    data_path = '../law_data/legal_advice.json'
    save_path = '../law_data/legal_advice_completed.json'
    preprocessor = JsonPreprocessor(data_path=data_path,
                                    save_path=save_path)
    preprocessor.process(True)
