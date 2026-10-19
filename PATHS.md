# lucydiary2026 폴더 구조 (웹앱마다 자기 폴더)

폰에서 웹앱(홈 화면 설치)이 서로 막지 않도록 앱마다 폴더를 따로 쓴다. 같은 폴더에 두 앱을 두면 크롬이 한 묶음으로 봐서 먼저 설치한 앱만 설치된다.

| 앱 | 폴더 (주소) | 본 파일 |
|---|---|---|
| 루시 스페이스 | `space/` | `space/index.html` (+ `space/dream/` 사진) |
| 루시의 작업실 | `novel/` | `novel/index.html` |
| 시놉시스(에피소드 기획 보드) | `synop/` | `synop/index.html` |
| 정산(Royalty Manager Pro) | `royalty/` | `royalty/index.html` |
| 일정 매니저 | `mobile/` | `mobile/index.html` |
| 집필 일정 계산기 | `schedule/` | `schedule/index.html` |

- 맨 위 `index.html`은 `space/`로 넘겨 주는 안내 페이지일 뿐이다. **여기에 앱 파일을 덮어쓰지 말 것.**
- 예전 `novel.html` / `synop.html` / `royalty.html` 은 없다. 옛 위치에 올리면 안 보인다.
- 각 폴더 안 파일 이름은 예전과 같다: `novel-manifest.json`, `novel-sw.js`, `manifest.json`, `sw.js`, `royalty-manifest.json`, `royalty-sw.js`, `space-manifest.json`, `space-sw.js`, 아이콘 파일.
- 앱끼리 가리키는 주소: 작업실은 시놉을 `../synop/` 로 iframe에 끼운다.
- 서비스워커가 미리 받아 두는 목록은 `./` (폴더 기본 페이지)를 쓴다. 앱 파일 이름을 바꾸면 목록도 같이 고칠 것.
