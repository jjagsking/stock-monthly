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


def monthly_rates(df, months):
    if df is None or df.empty or "Close" not in df:
        return [None] * len(months)
    s = pd.to_numeric(df["Close"], errors="coerce").dropna()
    if s.empty:
        return [None] * len(months)
    idx = pd.DatetimeIndex(s.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    s.index = idx.to_period("M")
    s = s.groupby(level=0).last()
    out = []
    for m in months:
        p, c = (m - pd.DateOffset(months=1)).to_period("M"), m.to_period("M")
        out.append((float(s[c]) / float(s[p]) - 1) * 100
                   if p in s.index and c in s.index and s[p] > 0 else None)
    return out

def fred_rates(months):
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXKOUS"
    fx = pd.read_csv(url, parse_dates=["observation_date"], na_values=["."])
    fx = fx.set_index("observation_date")["DEXKOUS"]
    fx = pd.to_numeric(fx, errors="coerce").dropna()
    s = fx.groupby(fx.index.to_period("M")).last()
    out = []
    for m in months:
        p, c = (m - pd.DateOffset(months=1)).to_period("M"), m.to_period("M")
        out.append((float(s[c]) / float(s[p]) - 1) * 100
                   if p in s.index and c in s.index and s[p] > 0 else None)
    return out

def get_one(ticker, months):
    first = months[0] - pd.DateOffset(months=1)
    last = months[-1] + pd.DateOffset(months=1)
    start, end = first.strftime("%Y-%m-%d"), last.strftime("%Y-%m-%d")
    if ticker == "KRW=X":
        try:
            return ticker, fred_rates(months), "FRED DEXKOUS (달러당 원화 월말 관측치)"
        except Exception as e:
            return ticker, [None]*6, f"FRED 조회 실패: {str(e)[:70]}"
    if ticker == "^KS200":
        try:
            import FinanceDataReader as fdr
            df = fdr.DataReader("KS200", start, end)
            return ticker, monthly_rates(df, months), "FinanceDataReader KS200"
        except Exception as e:
            return ticker, [None]*6, f"KS200 조회 실패: {str(e)[:70]}"
    try:
        df = yf.Ticker(ticker).history(start=start, end=end, interval="1mo",
                                      auto_adjust=False, actions=False, raise_errors=False)
        vals = monthly_rates(df, months)
        if any(v is None for v in vals):
            daily = yf.Ticker(ticker).history(start=start, end=end, interval="1d",
                                             auto_adjust=False, actions=False, raise_errors=False)
            fallback = monthly_rates(daily, months)
            vals = [v if v is not None else fallback[i] for i, v in enumerate(vals)]
        return ticker, vals, "Yahoo Finance"
    except Exception as e:
        return ticker, [None]*6, f"조회 실패: {str(e)[:70]}"

@st.cache_data(ttl=3600, show_spinner=False)
def fetch(year, month):
    months = [pd.Timestamp(year, month, 1) + pd.DateOffset(months=i) for i in range(6)]
    results = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = {pool.submit(get_one, ticker, months): ticker for ticker, _ in ALL}
        for job in as_completed(jobs):
            ticker = jobs[job]
            try:
                _, values, note = job.result()
            except Exception as e:
                values, note = [None]*6, f"조회 실패: {str(e)[:70]}"
            results[ticker] = (values, note)
    return months, results

st.title("📈 월간 주식 등락률")
st.caption("기본 20개 고정 · 나머지 131개 선택 월 등락률순 · 6개월 비교")

# 연월을 주소에 보존합니다. 재방문 시 같은 주소를 열면 선택값이 유지됩니다.
def valid_date(y, m):
    try:
        return 1990 <= int(y) <= date.today().year and 1 <= int(m) <= 12
    except (ValueError, TypeError):
        return False

qp_y, qp_m = st.query_params.get("year"), st.query_params.get("month")
if valid_date(qp_y, qp_m):
    default_y, default_m = int(qp_y), int(qp_m)
else:
    default_y, default_m = 2013, 8

with st.form("month_form"):
    c1, c2 = st.columns(2)
    with c1:
        year = st.number_input("연도", min_value=1990, max_value=date.today().year,
                               value=default_y, step=1)
    with c2:
        month = st.selectbox("월", list(range(1, 13)), index=default_m - 1,
                             format_func=lambda x: f"{x}월")
    submit = st.form_submit_button("6개월 조회", type="primary", use_container_width=True)

if submit:
    st.query_params["year"] = str(int(year))
    st.query_params["month"] = str(int(month))

if submit or valid_date(st.query_params.get("year"), st.query_params.get("month")):
    yy, mm = int(st.query_params["year"]), int(st.query_params["month"])
    with st.spinner(f"{yy}년 {mm}월부터 6개월 조회 중..."):
        months, values = fetch(yy, mm)
    rows = [(ticker, name, *values.get(ticker, ([None]*6, "데이터 없음")))
            for ticker, name in ALL]
    selected = lambda row: row[2][0]
    ordered = rows[:len(BASE)] + sorted(rows[len(BASE):], key=lambda r: (
        selected(r) is None, -(selected(r) if selected(r) is not None else 0)))
    available = sum(selected(r) is not None for r in ordered)
    st.caption(f"{yy}년 {mm}월 기준 · {len(ordered)}개 종목 중 {available}개 수익률 조회")
    st.caption("좌우로 밀면 다음 월이 보입니다. 선택 월 기준으로 정렬·행 배경색이 결정됩니다.")
    style = """
    <style>
    .asset-scroll{width:100%;overflow-x:auto;overscroll-behavior-x:contain;border:1px solid #ddd;border-radius:8px}
    .asset-table{border-collapse:separate;border-spacing:0;min-width:690px;width:max-content;font-size:12px;line-height:1.35}
    .asset-table th,.asset-table td{padding:9px 6px;border-bottom:1px solid rgba(100,100,100,.12);white-space:nowrap;text-align:right}
    .asset-table th{background:#f0f1f4;color:#222;position:sticky;top:0;z-index:3}
    .asset-table .ticker{position:sticky;left:0;text-align:left;min-width:74px;width:74px;max-width:74px;z-index:2;font-weight:600}
    .asset-table .name{position:sticky;left:74px;text-align:left;min-width:104px;width:104px;max-width:104px;overflow:hidden;text-overflow:ellipsis;z-index:2}
    .asset-table th.ticker,.asset-table th.name{z-index:4;background:#f0f1f4}
    .asset-table td.month{min-width:77px;width:77px;font-variant-numeric:tabular-nums;font-weight:650}
    .asset-table .up{color:#c62828}.asset-table .down{color:#1565c0}.asset-table .zero{color:#555}
    .asset-table tr.positive td{background:#fff0f0}.asset-table tr.negative td{background:#edf4ff}
    .asset-table tr.neutral td{background:#f6f6f6}
    .asset-table th.selected{background:#e3e5ea}
    </style>
    """
    headers = ''.join(f'<th class="{ "selected" if i == 0 else ""}">{m.year}년 {m.month}월</th>'
                      for i, m in enumerate(months))
    html_rows = []
    for ticker, name, rates, note in ordered:
        base = rates[0]
        row_class = "neutral" if base is None or base == 0 else ("positive" if base > 0 else "negative")
        cells = []
        for rate in rates:
            cl = "zero" if rate is None or rate == 0 else ("up" if rate > 0 else "down")
            value = "—" if rate is None else f"{rate:+.1f}%"
            cells.append(f'<td class="month {cl}">{value}</td>')
        html_rows.append(f'<tr class="{row_class}"><td class="ticker">{html.escape(ticker)}</td>'
                         f'<td class="name" title="{html.escape(name, quote=True)}">{html.escape(name)}</td>'
                         + ''.join(cells) + '</tr>')
    st.markdown(style + '<div class="asset-scroll"><table class="asset-table"><thead><tr>'
                '<th class="ticker">티커</th><th class="name">종목명</th>' + headers + '</tr></thead><tbody>'
                + ''.join(html_rows) + '</tbody></table></div>', unsafe_allow_html=True)
    fx = values.get("KRW=X", ([None]*6, "조회 실패"))
    st.caption("달러/원: " + fx[1])
    missing = [(ticker, note) for ticker, _, rates, note in ordered if rates[0] is None]
    if missing:
        with st.expander(f"선택 월 미조회 종목 ({len(missing)}개)"):
            for ticker, note in missing:
                st.text(f"{ticker}: {note if note != 'Yahoo Finance' else '상장 전 또는 데이터 없음'}")
    columns = [f"{m.year}-{m.month:02d} 등락률(%)" for m in months]
    export = pd.DataFrame([{"티커":ticker, "종목명":name,
                            **{columns[i]: rates[i] for i in range(6)}, "데이터 출처":note}
                           for ticker, name, rates, note in ordered])
    st.download_button("6개월 CSV 다운로드", export.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"monthly_{yy}_{mm:02d}_6months.csv",
                       mime="text/csv", use_container_width=True)

st.caption("선택 연월은 웹주소에 저장됩니다. 그 주소를 즐겨찾기하면 다음 방문에도 같은 연월로 열립니다.")
st.caption("달러/원: FRED DEXKOUS · 코스피200: FinanceDataReader KS200 · 금: GLD ETF(달러 기준)")
