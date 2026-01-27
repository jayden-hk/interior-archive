import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json
import os
from PIL import Image
from io import BytesIO

# ==========================================
# 1. 설정 (여기에 API 키를 넣으세요)
# ==========================================
API_KEY = "AIzaSyCxBoYiwaVpkFMkretVQH5qrg4HP1_ZPqo"
genai.configure(api_key=API_KEY)

# ==========================================
# 2. AI 모델 설정 (Gemini 1.5 Flash - 빠르고 저렴)
# ==========================================
model = genai.GenerativeModel('gemini-1.5-flash')

def get_image_from_url(url):
    """웹사이트 URL에서 가장 큰 이미지(대표 이미지)를 찾아냅니다."""
    try:
        # 1. 이미지가 직접 입력된 경우
        if url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            return url
        
        # 2. 웹페이지인 경우 크롤링
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # og:image (SNS 공유용 이미지)를 우선 찾음
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]
            
        print("❌ 이미지를 찾지 못했습니다. 이미지 주소를 직접 입력해주세요.")
        return None
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return None

def analyze_image_with_ai(img_url):
    """이미지를 AI에게 보여주고 태그를 뽑아냅니다."""
    print(f"🤖 AI가 이미지를 분석 중입니다... ({img_url})")
    
    try:
        # 이미지 다운로드 (AI에게 보내기 위해)
        response = requests.get(img_url)
        img_data = Image.open(BytesIO(response.content))

        # 프롬프트 (질문)
        prompt = """
        Analyze this interior design image and provide a JSON response.
        Extract these fields:
        1. title: A creative short title (e.g., "Minimalist Wood Cafe")
        2. tags: Combine these categories into a single string separated by " | "
           - Space Type (e.g., Hotel, Home, Office, Cafe, Retail)
           - Key Material (e.g., Wood, Concrete, Marble, Metal)
           - Color Tone (e.g., Warm Beige, Dark Grey, White)
           - Country (Guess based on style, verify if text visible, default to 'Global')
        
        Example Output Format:
        {"title": "Cozy Nordic Living Room", "tags": "Home | Wood | Beige | Sweden"}
        """
        
        response = model.generate_content([prompt, img_data])
        # 응답에서 JSON 부분만 정리 (혹시 모를 공백 제거)
        text_res = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text_res)
        
    except Exception as e:
        print(f"❌ AI 분석 실패: {e}")
        return None

def update_json_file(new_data):
    """data.json 파일을 열어서 내용을 추가합니다."""
    file_path = 'data.json' # 같은 폴더에 있어야 함
    
    # 기존 데이터 읽기
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                data = []
    else:
        data = []
    
    # 새 데이터 추가
    data.insert(0, new_data) # 맨 앞에 추가 (최신순)
    
    # 저장하기
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("✅ data.json 파일 업데이트 완료!")

# ==========================================
# 3. 메인 실행
# ==========================================
if __name__ == "__main__":
    print("--- Sconee Archive Auto-Updater ---")
    target_url = input("🔗 분석할 웹사이트 또는 이미지 URL을 입력하세요: ")
    
    final_img_url = get_image_from_url(target_url)
    
    if final_img_url:
        ai_result = analyze_image_with_ai(final_img_url)
        
        if ai_result:
            # 결과 합치기
            entry = {
                "title": ai_result.get("title", "Untitled Space"),
                "tags": ai_result.get("tags", "Design | Global"),
                "img": final_img_url
            }
            
            print(f"\n✨ 결과 미리보기:\n제목: {entry['title']}\n태그: {entry['tags']}")
            update_json_file(entry)
            print("\n🚀 [다음 할 일] GitHub에 data.json 파일을 업로드하면 사이트가 바뀝니다!")
