import google.generativeai as genai

# 여기에 아까 받은 API 키를 넣으세요
API_KEY = "AIzaSyCxBoYiwaVpkFMkretVQH5qrg4HP1_ZPqo"
genai.configure(api_key=API_KEY)

print("--- 사용 가능한 AI 모델 목록 ---")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)