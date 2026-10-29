import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
import html
import warnings

st.set_page_config(page_title="월간 주식 등락률", page_icon="📈", layout="centered")
BASE = [('AAPL', '애플'), ('MSFT', '마이크로소프트'), ('NVDA', '엔비디아'), ('AMZN', '아마존'), ('GOOGL', '알파벳'), ('META', '메타'), ('TSLA', '테슬라'), ('NFLX', '넷플릭스'), ('AMD', 'AMD'), ('INTC', '인텔'), ('AVGO', '브로드컴'), ('QCOM', '퀄컴'), ('^KS200', '코스피200'), ('^NDX', '나스닥100'), ('^GSPC', 'S&P500'), ('^DJI', '다우존스'), ('GC=F', '금 선물'), ('KRW=X', '달러/원 환율'), ('005930.KS', '삼성전자'), ('000660.KS', 'SK하이닉스')]
EXTRA = [('PLTR', '팔란티어'), ('KO', '코카콜라'), ('SBUX', '스타벅스'), ('DDOG', '데이터독'), ('NET', '클라우드플레어'), ('TTD', '트레이드데스크'), ('ENPH', '엔페이즈'), ('LULU', '룰루레몬'), ('SPCX', '스페이스X'), ('F', '포드'), ('GM', '제너럴모터스'), ('RACE', '페라리'), ('UPS', 'UPS'), ('ISRG', '인튜이티브서지컬'), ('PANW', '팔로알토'), ('VRTX', '버텍스'), ('VZ', '버라이즌'), ('T', 'AT&T'), ('SONY', '소니'), ('TM', '토요타'), ('BIDU', '바이두'), ('MELI', '메르카도리브레'), ('EBAY', '이베이'), ('NOW', '서비스나우'), ('SHOP', '쇼피파이'), ('SPOT', '스포티파이'), ('CAT', '캐터필러'), ('MMM', '3M'), ('LMT', '록히드마틴'), ('FDX', '페덱스'), ('ABBV', '애브비'), ('UNH', '유나이티드헬스'), ('PEP', '펩시'), ('HD', '홈디포'), ('IBM', 'IBM'), ('TXN', '텍사스인스트루먼트'), ('GS', '골드만삭스'), ('MS', '모건스탠리'), ('WFC', '웰스파고'), ('XOM', '엑슨모빌'), ('CVX', '셰브론'), ('PFE', '화이자'), ('MRK', '머크'), ('QBTS', '디웨이브'), ('NKE', '나이키'), ('SFTBY', '소프트뱅크'), ('TCEHY', '텐센트'), ('QURE', '유니큐어'), ('MA', '마스터카드'), ('AXP', '아메리칸익스프레스'), ('RDDT', '레딧'), ('CRWV', '코어위브'), ('CRCL', '서클'), ('APP', '앱러빈'), ('SOUN', '사운드하운드'), ('OPEN', '오픈도어'), ('ASTS', 'AST스페이스모바일'), ('PYPL', '페이팔'), ('UPST', '업스타트'), ('SNAP', '스냅'), ('ABNB', '에어비앤비'), ('MRNA', '모더나'), ('NVAX', '노바백스'), ('TLRY', '틸레이'), ('WMT', '월마트'), ('COST', '코스트코'), ('DIS', '디즈니'), ('BA', '보잉'), ('BRK-B', '버크셔'), ('SMR', '뉴스케일파워'), ('OKLO', '오클로'), ('IONQ', '아이온큐'), ('RGTI', '리게티'), ('LUNR', '인튜이티브머신'), ('RKLB', '로켓랩'), ('DJT', '트럼프미디어'), ('LLY', '일라이릴리'), ('NVO', '노보노디스크'), ('ASML', 'ASML'), ('ARM', 'ARM'), ('CRWD', '크라우드스트라이크'), ('VST', '비스트라'), ('CEG', '컨스텔레이션에너지'), ('JPM', 'JP모건'), ('BAC', '뱅크오브아메리카'), ('PG', 'P&G'), ('JNJ', '존슨앤드존슨'), ('SNDK', '샌디스크'), ('WDC', '웨스턴디지털'), ('HIMS', '힘스앤허스'), ('VRT', '버티브'), ('ANET', '아리스타'), ('MRVL', '마벨'), ('AMAT', '어플라이드머티리얼즈'), ('GEV', 'GE버노바'), ('ORCL', '오라클'), ('CRM', '세일즈포스'), ('ADBE', '어도비'), ('MU', '마이크론'), ('COIN', '코인베이스'), ('MSTR', '마이크로스트래티지'), ('UBER', '우버'), ('MCD', '맥도날드'), ('V', '비자'), ('GME', '게임스탑'), ('AMC', 'AMC'), ('RIVN', '리비안'), ('LCID', '루시드'), ('PTON', '펠로톤'), ('ZM', '줌'), ('ROKU', '로쿠'), ('TSM', 'TSMC'), ('BB', '블랙베리'), ('NOK', '노키아'), ('CSCO', '시스코'), ('CPNG', '쿠팡'), ('PDD', '핀둬둬'), ('RIOT', '라이엇플랫폼'), ('SMCI', '슈퍼마이크로'), ('CVNA', '카바나'), ('BABA', '알리바바'), ('NIO', '니오'), ('PLUG', '플러그파워'), ('FSLR', '퍼스트솔라'), ('SPCE', '버진갤럭틱'), ('BYND', '비욘드미트'), ('SNOW', '스노우플레이크'), ('RBLX', '로블록스'), ('HOOD', '로빈후드'), ('SOFI', '소파이'), ('MARA', '마라홀딩스')]
print(f"기본 {len(BASE)}개 + 상승률 정렬 {len(EXTRA)}개 = 총 {len(BASE)+len(EXTRA)}개")
# GLD는 달러 기준 금 ETF. 기존 금 선물 대신 사용.
BASE = [("GLD", "금(GLD ETF)") if t == "GC=F" else (t, n) for t, n in BASE]
ALL = BASE + EXTRA

def month_closes(df, prev, cur):
    if df is None or df.empty or "Close" not in df:
        return None
    s = pd.to_numeric(df["Close"], errors="coerce").dropna()
    if s.empty:
        return None
    idx = pd.DatetimeIndex(s.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    s.index = idx.to_period("M")
    s = s.groupby(level=0).last()
    p, c = prev.to_period("M"), cur.to_period("M")
    if p not in s.index or c not in s.index or s[p] <= 0:
        return None
    return (float(s[c]) / float(s[p]) - 1) * 100

def get_one(ticker, prev, cur):
    end = (cur + pd.DateOffset(months=1)).strftime("%Y-%m-%d")
    start = prev.strftime("%Y-%m-%d")
    if ticker == "^KS200":
        try:
            import FinanceDataReader as fdr
            df = fdr.DataReader("KS200", start, end)
            r = month_closes(df, prev, cur)
            return ticker, r, "KRX/FinanceDataReader" if r is not None else "코스피200 데이터 없음"
        except Exception as e:
            return ticker, None, f"코스피200 조회 실패: {str(e)[:60]}"
    try:
        # 달러는 일봉 마지막 종가를 사용해 월봉 집계 차이를 회피.
        interval = "1d" if ticker == "KRW=X" else "1mo"
        df = yf.Ticker(ticker).history(start=start, end=end, interval=interval,
                                      auto_adjust=False, actions=False, raise_errors=False)
        r = month_closes(df, prev, cur)
        if r is None and interval == "1mo":
            df = yf.Ticker(ticker).history(start=start, end=end, interval="1d",
                                          auto_adjust=False, actions=False, raise_errors=False)
            r = month_closes(df, prev, cur)
        return ticker, r, "Yahoo Finance" if r is not None else "상장 전 또는 데이터 없음"
    except Exception as e:
        return ticker, None, f"조회 실패: {str(e)[:60]}"

@st.cache_data(ttl=3600, show_spinner=False)
def fetch(year, month):
    cur = pd.Timestamp(year, month, 1)
    prev = cur - pd.DateOffset(months=1)
    result = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        tasks = {pool.submit(get_one, t, prev, cur): t for t, _ in ALL}
        for future in as_completed(tasks):
            t = tasks[future]
            try:
                _, r, note = future.result()
            except Exception as e:
                r, note = None, f"조회 실패: {str(e)[:60]}"
            result[t] = (r, note)
    return result

st.title("📈 월간 주식 등락률")
st.caption("기존 20개 고정 순서 · 추가 131개 상승률순 · 월말 종가 기준")
c1, c2 = st.columns(2)
with c1:
    year = st.number_input("연도", min_value=1990, max_value=date.today().year, value=2013, step=1)
with c2:
    month = st.selectbox("월", list(range(1, 13)), index=7, format_func=lambda x: f"{x}월")
if st.button("조회", type="primary", use_container_width=True):
    st.session_state["requested"] = (int(year), int(month))

if "requested" in st.session_state:
    yy, mm = st.session_state["requested"]
    with st.spinner(f"{yy}년 {mm}월 전체 종목 조회 중..."):
        values = fetch(yy, mm)
    rows = [(t, n, *values.get(t, (None, "데이터 없음"))) for t, n in ALL]
    main = rows[:len(BASE)]
    additional = sorted(rows[len(BASE):], key=lambda r: (r[2] is None, -(r[2] or 0)))
    ordered = main + additional
    ok = sum(r[2] is not None for r in ordered)
    st.caption(f"{yy}년 {mm}월 · {len(ordered)}종목 중 {ok}개 조회")
    st.markdown("""
<style>
.asset-row{display:flex;align-items:center;justify-content:space-between;
border-radius:8px;padding:10px 12px;margin:3px 0;gap:8px;font-size:14px}
.asset-name{min-width:0;overflow-wrap:anywhere}
.asset-value{font-weight:700;white-space:nowrap}
.asset-up{background:#fff0f0;color:#c62828}
.asset-down{background:#edf4ff;color:#1565c0}
.asset-flat{background:#f5f5f5;color:#666}
</style>
""", unsafe_allow_html=True)
    output = []
    for ticker, name, rate, note in ordered:
        css = "asset-flat" if rate is None or rate == 0 else ("asset-up" if rate > 0 else "asset-down")
        display = "—" if rate is None else f"{rate:+.1f}%"
        output.append(f'<div class="asset-row {css}"><span class="asset-name">'
                      f'{html.escape(ticker)}　{html.escape(name)}</span>'
                      f'<span class="asset-value">{display}</span></div>')
    st.markdown("".join(output), unsafe_allow_html=True)
    failed = [(t, note) for t, _, r, note in ordered if r is None]
    if failed:
        with st.expander(f"미조회 종목 및 사유 ({len(failed)}개)"):
            for t, note in failed:
                st.text(f"{t}: {note}")
    csv = pd.DataFrame([{"티커":t, "종목명":n, "등락률(%)":r, "상태":note}
                        for t,n,r,note in ordered]).to_csv(index=False).encode("utf-8-sig")
    st.download_button("CSV 저장", csv, file_name=f"monthly_{yy}_{mm:02d}.csv",
                       mime="text/csv", use_container_width=True)
st.caption("금은 GLD 달러 기준 ETF(환율 미반영), 달러는 KRW=X 일봉 종가, 코스피200은 KRX KS200 사용. 게임 수치는 반영하지 않습니다.")
