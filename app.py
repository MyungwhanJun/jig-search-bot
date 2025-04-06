#PJT 찿기 정상 확인
#KAKAO 기반으로 바꾸기 [표시 형식]
#콘솔기반에서 Flask 기반으로 바꾸기
#환경변수에서 credentials.json 로딩으로 바꾸기
#이 코드는 Kakao 메시지 요청(JSON 형식)으로 PJT 코드를 받아서, 
# 해당 키워드(소문자 변환 후 비교)를 포함하는 행을 찾아 표 형식의 문자열로 응답합니다.

import os
import json
import gspread
from flask import Flask, request, jsonify
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# ✅ 구글 스프레드시트 읽기 권한 범위
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# ✅ 환경에 따라 credentials 처리 (환경변수 우선, 없으면 로컬 파일)
if os.environ.get("GOOGLE_CREDENTIALS_JSON"):
    google_creds = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    creds = Credentials.from_service_account_info(google_creds, scopes=SCOPES)
else:
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

gc = gspread.authorize(creds)

# ✅ Google Sheet ID와 시트 객체 초기화
spreadsheet_id = '1dT9t23zvfH5-dRBVE3QMcW3KHJwKLlmY1YVTa0fW0tk'
sheet = gc.open_by_key(spreadsheet_id).sheet1

@app.route("/", methods=["POST"])
def handle_kakao_request():
    req = request.get_json()
    # ✅ 사용자 입력 (대소문자 무시)
    pjt_keyword = req["userRequest"]["utterance"].strip().lower()
    
    # ✅ 전체 시트 불러오기
    data = sheet.get_all_values()
    
    # ✅ B열(PJT Code)에서 키워드(소문자 비교) 포함된 행 찾기
    matched_rows = []
    for idx, row in enumerate(data):
        if len(row) > 1 and pjt_keyword in row[1].lower():
            matched_rows.append(idx)
    
    if not matched_rows:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{
                    "simpleText": {
                        "text": f"❌ '{pjt_keyword}' 관련 결과를 찾을 수 없습니다."
                    }
                }]
            }
        })

    # ✅ 헤더 및 추출할 열 번호 정의
    headers = ['PJT', 'Front/Rear ', '회전측_로터', '아답터_코너', '고정측_CAL ', '고정측_DB  ', '고정측_RTV ', 'BCM_Fixture']
    cols_to_check = [2, 4, 5, 6, 7, 8, 9, 10]

    # ✅ 결과 데이터 추출
    table_data = [headers]
    for row_idx in matched_rows:
        row = data[row_idx]
        row_values = []
        for c in cols_to_check:
            col_idx = c - 1
            val = row[col_idx] if col_idx < len(row) else ''
            row_values.append(val)
        while len(row_values) < len(headers):
            row_values.append('')
        table_data.append(row_values)

    # ✅ 각 열의 최대 너비 계산 (표 정렬용)
    col_widths = [max(len(str(r[i])) for r in table_data) for i in range(len(headers))]

    def to_kakao_format_grouped(headers, table_data):
        output = ""
        for row in table_data[1:]:
            output += f"📋 {row[0]} 관련 지그 정보\n"
            for i in range(1, len(headers)):
                output += f"{headers[i]}: {row[i]}\n"
            output += "\n"
        output += "🤖 다른 지그의 차종을 입력해주세요!"
        return output

    message = to_kakao_format_grouped(headers, table_data)


    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [{
                "simpleText": {
                    "text": message
                }
            }]
        }
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
