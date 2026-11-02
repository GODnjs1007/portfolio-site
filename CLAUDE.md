# 작업 규칙

- 커밋 메시지에 `Co-Authored-By` 줄을 넣지 않는다.
- 커밋 작성자는 기존 git 설정 그대로 둔다.
- main에는 바로 올리지 않고, 새 브랜치에서 작업한 뒤 사용자가 확인하면 병합한다.
- 사용자가 요청하지 않은 변경은 하지 않는다.
- 사이트는 Hugo(PaperMod 테마는 건드리지 않음). 수정은 `layouts/`, `assets/css/extended/site.css`, `i18n/ko.toml`, `content/`에서만 한다.
- 화면 문구를 바꾼 뒤에는 `python3 scripts/check_copy.py`를 돌린다.
- 빌드·미리보기는 portfolio VM에서만 된다(맥북엔 hugo 없음).
