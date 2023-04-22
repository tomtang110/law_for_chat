
import argparse
import json
from tqdm import tqdm


class JsonPreprocessor:
    def __init__(self,data_path,save_path):
        self.data_path = data_path
        self.save_path = save_path

    @staticmethod
    def instruct_format_example(example: dict) -> dict:
        context = f"Instruction: {example['instruction']}\n"
        if example.get("input"):
            context += f"Input: {example['input']}\n"
        context += "Answer: "
        target = example["output"]
        return {"context": context, "target": target}

    def process(self):
        with open(self.data_path,encoding='utf-8') as f:
            examples = f.read()

        parsed_json = json.loads(examples)

        features = []
        for example in tqdm(parsed_json,desc='Processing'):
            feature = self.instruct_format_example(example)
            features.append(feature)

        with open(self.save_path,'w',encoding='utf-8') as p:
            p.write(json.dumps(features,ensure_ascii=False))



if __name__ == "__main__":
    preprocessor = JsonPreprocessor(data_path='../instruction_test_data/zh-data01.json',save_path='../instruction_test_data/zh-data01_completed.json')
    preprocessor.process()