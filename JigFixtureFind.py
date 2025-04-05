import gspread
from google.oauth2.service_account import Credentials

# 1. 구글 시트 연결
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
creds = Credentials.from_service_account_file(
    'D:/Coding Study/Chatbot/credentials.json',
    scopes=SCOPES
)
gc = gspread.authorize(creds)

# 2. 구글 시트 열기
spreadsheet_id = '1dT9t23zvfH5-dRBVE3QMcW3KHJwKLlmY1YVTa0fW0tk'
sheet = gc.open_by_key(spreadsheet_id).sheet1

# 3. 사용자 입력
pjt_keyword = input("필요한 PJT Code의 일부를 입력하세요: ").strip()

# 4. 시트 전체 데이터
data = sheet.get_all_values()

# 5. PJT Code(B열)에서 키워드를 포함하는 행 찾기
matched_rows = []
for idx, row in enumerate(data):
    if len(row) > 1 and pjt_keyword in row[1]:
        matched_rows.append(idx)

if not matched_rows:
    print(f"\n❌ '{pjt_keyword}'를 포함하는 PJT Code를 찾을 수 없습니다.")
    exit()

# 6. 고정 헤더와 열 위치 정의
headers = ['PJT', 'FRT/RR', '회전측', '아답터', '고정측_CAL', '고정측_DB', '고정측_RTV']
cols_to_check = [2, 4, 5, 6, 7, 8, 9]  # 엑셀 기준 (1-based), 실제 인덱스는 -1

# 7. 데이터 수집
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

# 8. 각 열의 최대 너비 계산
col_widths = [max(len(str(row[i])) for row in table_data) for i in range(len(headers))]

# 9. 출력 함수
def print_row(row):
    parts = [str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)]
    return " | ".join(parts)

# 10. 표 출력
print("\n📋 관련 정보:\n")

# 헤더
print(print_row(table_data[0]))

# 구분선
separator = "─" * (sum(col_widths) + 3 * (len(col_widths) - 1))
print(separator)

# 데이터
for row in table_data[1:]:
    print(print_row(row))

# 11. 다음 질문
print("\n🤖 찾고 싶은 지그의 차종이 무엇인가요?")
