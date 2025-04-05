import os
import json
import gspread
from flask import Flask, request, jsonify
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# ✅ 환경에 따라 credentials 처리
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

if os.environ.get("GOOGLE_CREDENTIALS_JSON"):
    # Render 환경 (환경변수 사용)
    google_creds = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    creds = Credentials.from_service_account_info(google_creds, scopes=SCOPES)
else:
    # 로컬 실행 (credentials.json 파일 사용)
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

gc = gspread.authorize(creds)

# Google Sheet ID
spreadsheet_id = '1dT9t23zvfH5-dRBVE3QMcW3KHJwKLlmY1YVTa0fW0tk'
sheet = gc.open_by_key(spreadsheet_id).sheet1

@app.route("/", methods=["POST"])
def handle_kakao_request():
    req = request.get_json()
    pjt_keyword = req["userRequest"]["utterance"].strip()

    # 전체 시트 불러오기
    data = sheet.get_all_values()

    # B열(PJT Code)에서 키워드 포함된 행 찾기
    matched_rows = []
    for idx, row in enumerate(data):
        if len(row) > 1 and pjt_keyword in row[1]:
            matched_rows.append(idx)

    if not matched_rows:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{
                    "simpleText": {
                        "text": f"❌ '{pjt_keyword}'를 포함하는 PJT Code를 찾을 수 없습니다."
                    }
                }]
            }
        })

    # 헤더와 열 번호 정의
    headers = ['PJT', 'FRT/RR', '회전측', '아답터', '고정측_CAL', '고정측_DB', '고정측_RTV']
    cols_to_check = [2, 4, 5, 6, 7, 8, 9]

    # 데이터 추출
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

    # 열 너비 정렬 계산
    col_widths = [max(len(str(row[i])) for row in table_data) for i in range(len(headers))]

    def to_kakao_format(headers, table_data, col_widths):
        output = "📋 관련 지그 정보\n\n"
        header_line = " ".join(f"[{headers[i].ljust(col_widths[i])}]" for i in range(len(headers)))
        output += header_line + "\n"
        for row in table_data[1:]:
            row_line = " ".join(f"{str(row[i]).ljust(col_widths[i])}" for i in range(len(headers)))
            output += row_line + "\n"
        output += "\n🤖 찾고 싶은 지그의 차종을 입력해주세요!"
        return output

    message = to_kakao_format(headers, table_data, col_widths)

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

# Flask 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
