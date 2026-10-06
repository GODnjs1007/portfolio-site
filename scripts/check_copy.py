#!/usr/bin/env python3
"""사이트 문구 점검기.

사용법 (저장소 루트에서):
    python3 scripts/check_copy.py            # 화면에 요약 출력 + docs/copy-review.md 생성
    python3 scripts/check_copy.py --quiet    # 파일만 생성

점검하는 것
  1. 깨진 문자        : 화면에 �(U+FFFD)로 보이는 글자
  2. 오타 후보        : 아래 TYPOS 목록에 있는 단어
  3. AI 말투 후보     : 아래 AI_TONE 목록의 표현 (사이트 문구에만 적용, 노션 원문은 제외)
  4. 남은 자리표시    : [작성 필요], 옮기지 못한 이미지 주석

목록은 아래 TYPOS / AI_TONE 에 직접 추가·삭제하면 된다.
코드 블록(``` ... ```) 안은 명령어라 검사하지 않는다.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# 일부러 쓴 깨진 문자(트러블슈팅 증상 그 자체)는 여기 넣어 검사에서 뺀다
ALLOW_BROKEN = ["물음표(\ufffd)"]

# 오타 후보: (정규식, 고칠 글자 제안)
TYPOS = [
    (r"설지\b|설지$", "설치"),
    (r"바뀜다", "바뀐다"),
    (r"곷", "곧"),
    (r"없앱다", "없앤다"),
    (r"서브티", "서브넷"),
    (r"트랙픽", "트래픽"),
    (r"되도(?=[\s,.]|$)", "돼도"),
    (r"않되", "안 되"),
    (r"몇일", "며칠"),
]

# AI 말투 후보: (정규식, 왜 걸리는지)
AI_TONE = [
    (r"그려두었습니다|담아두었습니다|모아두었습니다", "'~해두었습니다' 반복은 소개문 티가 남"),
    (r"서로 어떻게 이어지는지", "추상적인 표현. 무엇이 무엇으로 이어지는지 구체적으로"),
    (r"할 수 있습니다", "능력 나열체. 실제로 한 일로 바꾸기"),
    (r"다양한|효율적|체계적|원활한|최적의", "뜻이 넓은 수식어. 구체적인 사실로 대체"),
    (r"을 통해|를 통해", "번역투. '~로', '~해서'로 줄이기"),
    (r"여정|탐색|한눈에|손으로 직접", "광고 문구 느낌"),
    (r"—", "영어식 줄표(em dash). 한국어 문장에선 쉼표나 마침표로"),
    (r"뿐만 아니라|나아가|더 나아가", "연결어 과다"),
    (r"(습니다\.\s*){3,}", "'~습니다.'가 연속 3번 이상. 문장 길이·어미 섞기"),
    (r"직접", "'직접' 반복. 정말 강조할 곳만 남기기"),
]

# 사이트 문구(AI 말투 검사 대상) vs 노션 원문(오타·깨진 문자만 검사)
AUTHORED = [
    "i18n/ko.toml",
    "hugo.toml",
    "content/about.md",
    "content/projects/**/*.md",
    "content/notes/_index.md",
    "content/learned/_index.md",
]
ORIGINAL = [
    "content/notes/*/index.md",
    "content/notes/*/learned.md",
]


def files(patterns):
    out = []
    for p in patterns:
        out += sorted(ROOT.glob(p))
    return [f for f in out if f.is_file()]


def lines_outside_code(path):
    in_code = False
    for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            yield no, line


def rel(p):
    return str(p.relative_to(ROOT))


def main():
    quiet = "--quiet" in sys.argv
    broken, typos, tone, todo = [], [], [], []
    image_count = {}

    authored = files(AUTHORED)
    original = files(ORIGINAL)

    for f in authored + original:
        is_authored = f in authored
        for no, line in lines_outside_code(f):
            where = f"{rel(f)}:{no}"
            if "\ufffd" in line and not any(a in line for a in ALLOW_BROKEN):
                broken.append((where, line.strip()))
            for bad, good in TYPOS:
                m = re.search(bad, line)
                if m:
                    typos.append((where, m.group(0), good, line.strip()))
            if "[작성 필요]" in line:
                todo.append((where, line.strip()))
            if "<!-- 이미지" in line:
                image_count[rel(f)] = image_count.get(rel(f), 0) + 1
            if is_authored and not line.lstrip().startswith(("#", "<!--")):
                for pat, why in AI_TONE:
                    if re.search(pat, line):
                        tone.append((where, why, line.strip()))

    out = ["# 문구 점검 결과", "", "`python3 scripts/check_copy.py`로 다시 만들 수 있다. 고친 뒤 다시 돌려서 0건이 되는지 확인.", ""]

    def section(title, rows, fmt):
        out.append(f"## {title} ({len(rows)}건)")
        out.append("")
        if not rows:
            out.append("없음")
        for r in rows:
            out.append(fmt(r))
        out.append("")

    section("1. 깨진 문자 (�)", broken, lambda r: f"- `{r[0]}` — {r[1]}")
    section("2. 오타 후보 (노션 원문 포함, 고칠지는 직접 판단)", typos, lambda r: f"- `{r[0]}` — **{r[1]}** → {r[2]}")
    section("3. AI 말투 후보 (사이트 문구만)", tone, lambda r: f"- `{r[0]}` — {r[1]}\n  > {r[2][:120]}")
    section("4. [작성 필요] 남은 곳", todo, lambda r: f"- `{r[0]}` — {r[1][:80]}")
    out.append(f"## 5. 옮기지 못한 이미지 ({sum(image_count.values())}곳)")
    out.append("")
    for k, v in sorted(image_count.items()):
        out.append(f"- `{k}` — {v}곳")
    out.append("")

    report = ROOT / "docs" / "copy-review.md"
    report.write_text("\n".join(out), encoding="utf-8")

    if not quiet:
        print(f"깨진 문자 {len(broken)} · 오타 후보 {len(typos)} · AI 말투 후보 {len(tone)} · "
              f"작성 필요 {len(todo)} · 이미지 {sum(image_count.values())}")
        print(f"자세한 목록: {rel(report)}")


if __name__ == "__main__":
    main()
