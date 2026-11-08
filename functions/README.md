# 정산 앱 「투고하기」 메일 발송 서버 설정

앱의 「웹툰 투고 → 투고하기」 버튼이 네이버 메일로 PDF를 첨부해 발송하도록 하는 서버예요. 한 번만 설정하면 돼요.

## 준비물
1. **네이버 메일 설정**: 네이버 메일 → 환경설정 → POP3/IMAP 설정 → **SMTP 사용 = 사용함**
2. **비밀번호**: 2단계 인증을 켠 계정은 「애플리케이션 비밀번호」를, 2단계 인증을 쓰지 않는 계정은 로그인 비밀번호를 써요. (비밀번호는 서버 비밀 저장소에만 들어가요)
3. **파이어베이스 요금제**: 프로젝트 `writer-routine`을 **Blaze(종량제)** 로 바꿔야 함수가 배포돼요. 이 정도 사용량이면 사실상 0원이에요.
4. **Cloud Storage 켜기**: 파이어베이스 콘솔 → Storage → 시작하기 (PDF 보관용)
5. PC에 Node.js 20 이상 + `npm i -g firebase-tools`

## 배포 (PC 터미널에서, 이 저장소 폴더에서)
```
firebase login
cd functions && npm install && cd ..
firebase functions:secrets:set NAVER_ACC_1    # 계정 1: 네이버아이디|비밀번호   (예: myid|abcd1234)
firebase functions:secrets:set NAVER_ACC_2    # 계정 2: 같은 형식 (안 쓰면 none|none)
firebase functions:secrets:set NAVER_ACC_3    # 계정 3: 같은 형식 (안 쓰면 none|none)
firebase functions:secrets:set MAIL_KEY       # 앱과 서버가 나눌 비밀 열쇠 (아무 긴 문자열, 직접 정해요)
firebase deploy --only functions
```
배포가 끝나면 함수 주소가 3개 나와요 (`sendMail`, `uploadPdf`, `pdfInfo`). **`sendMail` 주소만** 앱에 넣으면 돼요.

## 앱에서 (웹 · PC · 폰 각각 한 번)
웹툰 투고 → 작품 선택 → **투고하기** → 오른쪽 위 ⚙ → `sendMail` 주소 + 비밀 열쇠 입력 → 저장
같은 창에서 **필명마다 계정(1·2·3)** 을 골라 주세요. (이 연결은 앱 데이터라 다른 기기에도 같이 적용돼요)
보내는 이름은 작품의 필명 그대로 나가요.
