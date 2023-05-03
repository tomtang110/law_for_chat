import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

import json
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64)\
 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}

url = 'https://www.66law.cn/laws/hunyinjiating/jiehun/jhtj/'

origin_url = 'https://www.66law.cn'

sesson = requests.Session()
retry = Retry(connect=3,backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
sesson.mount("http://",adapter)
sesson.mount("https://",adapter)
# page = requests.get(url,headers=headers)



contents = []
# print(soup)

page_num_start = 1
page_num_end = 2
instructs = []
inputs = []
contexts = []
for i in range(page_num_start,page_num_end+1):
    page_url = url + 'page_{}.aspx'.format(i)
    page = sesson.get(page_url,headers=headers)
    soup = BeautifulSoup(page.content,'html.parser')
    results = soup.find(attrs={'class':'cx-tw-list li-ptb30 mt10'})
    print('page {} is dealing'.format(i))
    context_list = []
    t = 1
    for child in results.children:
        if isinstance(child,str):continue
        new_ref = child.select_one("a").get("href")
        content_ref = origin_url + new_ref
        page_c = sesson.get(content_ref,headers=headers)
        soup_c = BeautifulSoup(page_c.content,'html.parser')
        child_c = soup_c.find(attrs={'class':'det-title'})
        q_name = child_c.find('h1').get_text().strip()
        if q_name == "假结婚的后果有哪些":
            print('debg')
        print('{} case is dealing'.format(t))
        t += 1
        context_c = soup_c.find(attrs={'class':'det-nr'})
        context_list = []
        for context_child in context_c.children:
            if isinstance(context_child, str): continue

            c_input = context_child.find('strong')
            if c_input:
                c_i = c_input.get_text().strip()
                if (len(c_i)) < 1:continue
                if c_i.startswith("【温馨提示】")  or '华律网' in c_i:continue
                inputs.append(c_i)
                instructs.append(q_name)
                if context_list:
                    contexts.append('\n'.join(context_list))
                context_list = []
                continue
            text = context_child.text
            if text.startswith("【温馨提示】") or '华律网' in text: continue
            context_list.append(text)

        if context_list:
            contexts.append('\n'.join(context_list))
        print(len(inputs))
        print(len(contexts))


assert len(inputs) == len(contexts)

print('total {} inputs'.format(len(inputs)))
features = []

for i in range(len(inputs)):
    context = f"Instruction: {inputs[i]}\n"
    context += 'Input: """\n"'
    context += "Answer: "
    target = contexts[i]
    features.append({"context": context, "target": target})

with open('../data/marriage_law_1_10.json', 'w', encoding='utf-8') as p:
    p.write(json.dumps(features, ensure_ascii=False))


