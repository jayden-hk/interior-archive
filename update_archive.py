import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json
import os
import shutil
import subprocess
from PIL import Image
from io import BytesIO
import time

# ==========================================
# 1. 설정 (API 키 확인!)
# ==========================================
API_KEY = "AIzaSyDDS9bCqH0FE9wNZhSvAMWDScHytvYYnUM"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') 

# 폴더 설정 (로컬 업로드용)
INPUT_FOLDER = 'my_uploads'      # 사진 넣는 곳
OUTPUT_FOLDER = 'images'         # 웹용 압축 저장소
PROCESSED_FOLDER = 'processed'   # 처리 완료된 원본 보관소

# ==========================================
# 2. 공통 기능 (AI 분석 및 JSON 저장)
# ==========================================
def analyze_image_data(img_data, source_name):
    """이미지 데이터(Bytes)를 받아서 AI 분석을 수행합니다."""
    print(f"🤖 AI 정밀 분석 중... ({source_name})")
    try:
        prompt = """
        Analyze this interior image and output a JSON object with these specific keys:
        1. title: A creative short title.
        2. space: The specific type of space (e.g., Living Room, Hotel Lobby, Office, Cafe, Kitchen).
        3. vibe: The atmosphere or style (e.g., Minimalist, Industrial, Cozy, Luxury, Rustic).
        4. detail: Key materials or dominant colors (e.g., Wood & Marble, Dark Grey, Beige & White).
        
        Example Output:
        {"title": "Cozy Wooden Loft", "space": "Home", "vibe": "Rustic", "detail": "Wood & Green"}
        """
        response = model.generate_content([prompt, img_data])
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"   ❌ 분석 실패: {e}")
        return None

def update_json_file(new_data):
    file_path = 'data.json'
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try: data = json.load(f)
            except: data = []
    else:
        data = []
    
    data.insert(0, new_data)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ==========================================
# 3. 트랙 A: 인터넷 URL 처리 기능
# ==========================================
def process_url_image(url):
    try:
        # 사람인 척 위장하는 헤더
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.google.com/'
        }
        
        # 1. 이미지 주소 찾기 (HTML인 경우)
        if not url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                url = og_image["content"]
            else:
                return None

        # 2. 이미지 다운로드 및 분석
        img_res = requests.get(url, headers=headers, timeout=10)
        img_data = Image.open(BytesIO(img_res.content))
        
        result = analyze_image_data(img_data, "URL")
        
        if result:
            entry = {
                "title": result.get("title"),
                "space": result.get("space", "Space"),
                "vibe": result.get("vibe", "Style"),
                "detail": result.get("detail", "Detail"),
                "img": url # URL 방식은 인터넷 주소 그대로 사용
            }
            update_json_file(entry)
            print(f"   ✅ URL 처리 완료: {entry['title']}")
            return True
            
    except Exception as e:
        print(f"   ⚠️ URL 접속 에러: {e}")
    return False

# ==========================================
# 4. 트랙 B: 내 컴퓨터 파일 처리 기능
# ==========================================
def process_local_file(filename):
    src_path = os.path.join(INPUT_FOLDER, filename)
    target_path = os.path.join(OUTPUT_FOLDER, filename)
    
    # 폴더 없으면 생성
    if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
    if not os.path.exists(PROCESSED_FOLDER): os.makedirs(PROCESSED_FOLDER)

    try:
        # 1. 이미지 최적화 (압축)
        with Image.open(src_path) as img:
            img = img.convert('RGB')
            if max(img.size) > 1600: img.thumbnail((1600, 1600))
            img.save(target_path, "JPEG", quality=85)
            
            # 분석을 위해 열린 이미지 객체 사용
            result = analyze_image_data(img, filename)
            
        if result:
            # 2. JSON 저장 (로컬 경로 사용)
            entry = {
                "title": result.get("title"),
                "space": result.get("space", "Space"),
                "vibe": result.get("vibe", "Style"),
                "detail": result.get("detail", "Detail"),
                "img": f"images/{filename}" # 내 사이트 내부 경로
            }
            update_json_file(entry)
            
            # 3. 원본 이동 (중복 방지)
            shutil.move(src_path, os.path.join(PROCESSED_FOLDER, filename))
            print(f"   ✅ 로컬 파일 처리 완료: {entry['title']}")
            return True
            
    except Exception as e:
        print(f"   ❌ 로컬 파일 에러 ({filename}): {e}")
    return False

# ==========================================
# 5. 메인 실행 (하이브리드 모드)
# ==========================================
def push_to_github():
    print("\n🚀 GitHub에 모든 변경사항 업로드 중...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Hybrid Update"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🎉 업로드 완료! 사이트에서 확인하세요.")
    except Exception as e:
        print(f"⚠️ 업로드 실패: {e}")

if __name__ == "__main__":
    print("--- Sconee Archive Hybrid Updater ---")
    print("1. list.txt의 URL을 확인합니다.")
    print("2. my_uploads 폴더의 사진을 확인합니다.\n")
    
    total_success = 0

    # [Track A] URL 처리
    if os.path.exists('list.txt'):
        with open('list.txt', 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        
        if urls:
            print(f"🌐 인터넷 주소 {len(urls)}개 발견! 작업을 시작합니다.")
            for url in urls:
                if process_url_image(url):
                    total_success += 1
                    time.sleep(1)
            # list.txt 비우기
            with open('list.txt', 'w', encoding='utf-8') as f: f.write("")
        else:
            print("🌐 list.txt가 비어있습니다. (패스)")

    # [Track B] 로컬 파일 처리
    if not os.path.exists(INPUT_FOLDER): os.makedirs(INPUT_FOLDER)
    
    local_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    if local_files:
        print(f"\n📁 내 컴퓨터 사진 {len(local_files)}장 발견! 작업을 시작합니다.")
        for file in local_files:
            if process_local_file(file):
                total_success += 1
                time.sleep(1)
    else:
        print("\n📁 my_uploads 폴더가 비어있습니다. (패스)")

    # 마무리
    if total_success > 0:
        print(f"\n✨ 총 {total_success}건의 작업을 성공적으로 마쳤습니다.")
        push_to_github()
    else:
        print("\n🤔 처리할 작업이 없습니다. list.txt나 my_uploads 폴더를 채워주세요.")