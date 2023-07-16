# 大模型法律项目开发
本项目主要研究大模型在单独的法律数据集上的效果，现在支持belle和chatglm相关的模型训练，预测，验证和在线部署， 另外增加爬虫代码，langchain，结合数据库预测等功能。

因为设备的原因，本研究仅限制在了6B以下的模型。 

主要实验的模型包括chatllma, bloomz, chatGLM。

chatllma和bloomz相关模型（包括lora）可以在belle文件夹内参考readme进行训练和预测

chatglm相关实验（包括ptuning算法）可以在ptuning文件夹参考readme进行训练和预测

WebScraper文件夹是相关法律内容的爬虫代码，可以直接从定制的网页爬取法律数据集。

chatglm-web可以支持模型的在线部署， 先启动run_backend.sh加载模型和启动服务， 后启动run_frontend.sh开启前端页面。

langchain-ChatGLM项目支持利用数据库和大模型的结合预测方式。

## 一些实验结论
1. 对于ptuning而言， 泛化性较差，不建议直接拿新数据在ptuning上做finetune，很容易出现乱码字体或者一直重复生成某些关键字。
2. Lora相对而言，泛化性要好一点，但是在资源充足情况下，建议8卡A100，直接冲。
3. 数据质量非常的关键，如果数据质量不好，很容易导致模型（finetune）被污染。
4. 在资源不够大模型全部参数更新的情况下，用小模型的效果训练全部参数效果可能是优于用p-tuning或者lora的大模型效果。
5. 在问答问题和打标任务上，大模型在新数据的效果上，问题问题是弱于打标任务的，在设计好打标任务的prompt后，打标任务是很容易被学习的。

# 有兴趣研究大模型的可以知乎关注 Tang AI

https://www.zhihu.com/people/tang-ai-3-14


