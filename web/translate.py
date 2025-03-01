# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("translation", model="ModelSpace/GemmaX2-28-2B-v0.1")


# Load model directly
from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "ModelSpace/GemmaX2-28-2B-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_id)

model = AutoModelForCausalLM.from_pretrained(model_id)

text = "Translate this from Chinese to English:\nChinese: 我爱机器翻译\nEnglish:"
inputs = tokenizer(text, return_tensors="pt")

outputs = model.generate(**inputs, max_new_tokens=50)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))


