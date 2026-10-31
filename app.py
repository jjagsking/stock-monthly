import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
import html
import warnings
import streamlit.components.v1 as components

st.set_page_config(page_title="월간 주식 등락률", page_icon="📈", layout="centered")
BASE = [('AAPL', '애플'), ('MSFT', '마이크로소프트'), ('NVDA', '엔비디아'), ('AMZN', '아마존'), ('GOOGL', '알파벳'), ('META', '메타'), ('TSLA', '테슬라'), ('NFLX', '넷플릭스'), ('AMD', 'AMD'), ('INTC', '인텔'), ('AVGO', '브로드컴'), ('QCOM', '퀄컴'), ('^KS200', '코스피200'), ('^NDX', '나스닥100'), ('^GSPC', 'S&P500'), ('^DJI', '다우존스'), ('GC=F', '금 선물'), ('KRW=X', '달러/원 환율'), ('005930.KS', '삼성전자'), ('000660.KS', 'SK하이닉스')]
EXTRA = [('PLTR', '팔란티어'), ('KO', '코카콜라'), ('SBUX', '스타벅스'), ('DDOG', '데이터독'), ('NET', '클라우드플레어'), ('TTD', '트레이드데스크'), ('ENPH', '엔페이즈'), ('LULU', '룰루레몬'), ('SPCX', '스페이스X'), ('F', '포드'), ('GM', '제너럴모터스'), ('RACE', '페라리'), ('UPS', 'UPS'), ('ISRG', '인튜이티브서지컬'), ('PANW', '팔로알토'), ('VRTX', '버텍스'), ('VZ', '버라이즌'), ('T', 'AT&T'), ('SONY', '소니'), ('TM', '토요타'), ('BIDU', '바이두'), ('MELI', '메르카도리브레'), ('EBAY', '이베이'), ('NOW', '서비스나우'), ('SHOP', '쇼피파이'), ('SPOT', '스포티파이'), ('CAT', '캐터필러'), ('MMM', '3M'), ('LMT', '록히드마틴'), ('FDX', '페덱스'), ('ABBV', '애브비'), ('UNH', '유나이티드헬스'), ('PEP', '펩시'), ('HD', '홈디포'), ('IBM', 'IBM'), ('TXN', '텍사스인스트루먼트'), ('GS', '골드만삭스'), ('MS', '모건스탠리'), ('WFC', '웰스파고'), ('XOM', '엑슨모빌'), ('CVX', '셰브론'), ('PFE', '화이자'), ('MRK', '머크'), ('QBTS', '디웨이브'), ('NKE', '나이키'), ('SFTBY', '소프트뱅크'), ('TCEHY', '텐센트'), ('QURE', '유니큐어'), ('MA', '마스터카드'), ('AXP', '아메리칸익스프레스'), ('RDDT', '레딧'), ('CRWV', '코어위브'), ('CRCL', '서클'), ('APP', '앱러빈'), ('SOUN', '사운드하운드'), ('OPEN', '오픈도어'), ('ASTS', 'AST스페이스모바일'), ('PYPL', '페이팔'), ('UPST', '업스타트'), ('SNAP', '스냅'), ('ABNB', '에어비앤비'), ('MRNA', '모더나'), ('NVAX', '노바백스'), ('TLRY', '틸레이'), ('WMT', '월마트'), ('COST', '코스트코'), ('DIS', '디즈니'), ('BA', '보잉'), ('BRK-B', '버크셔'), ('SMR', '뉴스케일파워'), ('OKLO', '오클로'), ('IONQ', '아이온큐'), ('RGTI', '리게티'), ('LUNR', '인튜이티브머신'), ('RKLB', '로켓랩'), ('DJT', '트럼프미디어'), ('LLY', '일라이릴리'), ('NVO', '노보노디스크'), ('ASML', 'ASML'), ('ARM', 'ARM'), ('CRWD', '크라우드스트라이크'), ('VST', '비스트라'), ('CEG', '컨스텔레이션에너지'), ('JPM', 'JP모건'), ('BAC', '뱅크오브아메리카'), ('PG', 'P&G'), ('JNJ', '존슨앤드존슨'), ('SNDK', '샌디스크'), ('WDC', '웨스턴디지털'), ('HIMS', '힘스앤허스'), ('VRT', '버티브'), ('ANET', '아리스타'), ('MRVL', '마벨'), ('AMAT', '어플라이드머티리얼즈'), ('GEV', 'GE버노바'), ('ORCL', '오라클'), ('CRM', '세일즈포스'), ('ADBE', '어도비'), ('MU', '마이크론'), ('COIN', '코인베이스'), ('MSTR', '마이크로스트래티지'), ('UBER', '우버'), ('MCD', '맥도날드'), ('V', '비자'), ('GME', '게임스탑'), ('AMC', 'AMC'), ('RIVN', '리비안'), ('LCID', '루시드'), ('PTON', '펠로톤'), ('ZM', '줌'), ('ROKU', '로쿠'), ('TSM', 'TSMC'), ('BB', '블랙베리'), ('NOK', '노키아'), ('CSCO', '시스코'), ('CPNG', '쿠팡'), ('PDD', '핀둬둬'), ('RIOT', '라이엇플랫폼'), ('SMCI', '슈퍼마이크로'), ('CVNA', '카바나'), ('BABA', '알리바바'), ('NIO', '니오'), ('PLUG', '플러그파워'), ('FSLR', '퍼스트솔라'), ('SPCE', '버진갤럭틱'), ('BYND', '비욘드미트'), ('SNOW', '스노우플레이크'), ('RBLX', '로블록스'), ('HOOD', '로빈후드'), ('SOFI', '소파이'), ('MARA', '마라홀딩스')]
print(f"기본 {len(BASE)}개 + 상승률 정렬 {len(EXTRA)}개 = 총 {len(BASE)+len(EXTRA)}개")
# GLD는 달러 기준 금 ETF. 기존 금 선물 대신 사용.
BASE = [("GLD", "금(GLD ETF)") if t == "GC=F" else (t, n) for t, n in BASE]
BASE.append(("BTC-USD", "비트코인"))
ALL = BASE + EXTRA

# 사용자 제공 금 월별 상/하 기록. 00.10은 2000년 10월부터 시작합니다.
# 글자 하나가 해당 연도의 1월부터 한 달씩 대응합니다.
# 사진과 대조해 2000년 10~12월은 3개, 2003년은 12개월로 교정했습니다.
# 사진 판독이 불명확한 다른 구간은 사용자 제공 기록을 유지합니다.
# 누락된 월은 "미"로 표시합니다.
GOLD_RAW = {
    2000: (10, "상상상"),
    2001: (1, "미상하상상상상상상하하상"),
    2002: (1, "미상상상상하하상상상하상"),
    2003: (1, "상하하상상하하상상상상상"),
    2004: (1, "하상상하상상하상상하상"),
    2005: (1, "상상하상상상상상상하상상"),
    2006: (1, "상상하상하하상하하상상"),
    2007: (1, "상상하하하하상상상상하상"),
    2008: (1, "상상상하상상상상상상하상"),
    2009: (1, "상하하하상하상하상하상상"),
    2010: (1, "상상하상상하하상상상상"),
    2011: (1, "하상하상하하상상하상상"),
    2012: (1, "상상하하하상상상상상"),
    2013: (1, "상하상하하하상상하하하상"),
    2014: (1, "상상하상하상상상하하상상"),
    2015: (1, "상하하하상상하상하상"),
    2016: (1, "상상하상하하상하상하하상"),
    2017: (1, "상상하상상하상상하하상상"),
    2018: (1, "상하하상상하하하상하하상"),
    2019: (1, "상상상상하상상상하상하상"),
    2020: (1, "상하상상상상"),
    2021: (1, "상하하상상하상하하하상상"),
    2022: (1, "상상상하하하상상하하상"),
    2023: (1, "하상상상하하상상하상상상"),
    2024: (1, "상상상상상상상상상상하상"),
    2025: (1, "상상상상하상상상상상상상"),
    2026: (1, "상상상상상하하상하"),
}

def gold_month_status(month):
    info = GOLD_RAW.get(month.year)
    if info is None:
        return "미"
    first_month, sequence = info
    index = month.month - first_month
    if index < 0 or index >= 12 or index >= len(sequence):
        return "미"
    return "하" if sequence[index] in ("ㅎ", "하") else "상" if sequence[index] == "상" else "미"



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

ECOS_FX = {'1998-01': 1572.9, '1998-02': 1640.1, '1998-03': 1378.8, '1998-04': 1338.2, '1998-05': 1410.8, '1998-06': 1385.2, '1998-07': 1236.0, '1998-08': 1331.8, '1998-09': 1373.6, '1998-10': 1313.8, '1998-11': 1243.7, '1998-12': 1207.8, '1999-01': 1175.3, '1999-02': 1222.4, '1999-03': 1224.7, '1999-04': 1176.4, '1999-05': 1186.3, '1999-06': 1155.9, '1999-07': 1206.9, '1999-08': 1184.9, '1999-09': 1218.7, '1999-10': 1200.5, '1999-11': 1157.5, '1999-12': 1145.4, '2000-01': 1122.1, '2000-02': 1131.8, '2000-03': 1108.3, '2000-04': 1110.3, '2000-05': 1133.8, '2000-06': 1114.8, '2000-07': 1116.2, '2000-08': 1108.8, '2000-09': 1115.0, '2000-10': 1136.7, '2000-11': 1195.3, '2000-12': 1259.7, '2001-01': 1265.5, '2001-02': 1245.7, '2001-03': 1328.0, '2001-04': 1324.7, '2001-05': 1292.9, '2001-06': 1300.7, '2001-07': 1301.4, '2001-08': 1283.8, '2001-09': 1309.1, '2001-10': 1296.1, '2001-11': 1274.0, '2001-12': 1326.1, '2002-01': 1314.8, '2002-02': 1327.7, '2002-03': 1326.4, '2002-04': 1292.2, '2002-05': 1233.3, '2002-06': 1201.8, '2002-07': 1197.0, '2002-08': 1200.5, '2002-09': 1225.5, '2002-10': 1233.4, '2002-11': 1208.0, '2002-12': 1200.4, '2003-01': 1170.5, '2003-02': 1186.8, '2003-03': 1252.9, '2003-04': 1213.1, '2003-05': 1206.6, '2003-06': 1193.1, '2003-07': 1180.0, '2003-08': 1179.9, '2003-09': 1150.2, '2003-10': 1177.3, '2003-11': 1202.6, '2003-12': 1197.8, '2004-01': 1173.6, '2004-02': 1174.5, '2004-03': 1153.6, '2004-04': 1167.7, '2004-05': 1165.7, '2004-06': 1152.5, '2004-07': 1168.3, '2004-08': 1153.8, '2004-09': 1147.9, '2004-10': 1126.0, '2004-11': 1047.9, '2004-12': 1043.8, '2005-01': 1026.4, '2005-02': 1008.1, '2005-03': 1024.3, '2005-04': 1002.5, '2005-05': 1002.5, '2005-06': 1024.4, '2005-07': 1028.3, '2005-08': 1031.0, '2005-09': 1038.0, '2005-10': 1042.7, '2005-11': 1036.3, '2005-12': 1013.0, '2006-01': 971.0, '2006-02': 969.0, '2006-03': 975.9, '2006-04': 945.7, '2006-05': 947.4, '2006-06': 960.3, '2006-07': 953.1, '2006-08': 959.6, '2006-09': 945.2, '2006-10': 944.2, '2006-11': 929.9, '2006-12': 929.6, '2007-01': 940.9, '2007-02': 938.3, '2007-03': 940.3, '2007-04': 929.4, '2007-05': 929.9, '2007-06': 926.8, '2007-07': 923.2, '2007-08': 939.9, '2007-09': 920.7, '2007-10': 907.4, '2007-11': 929.6, '2007-12': 938.2, '2008-01': 943.9, '2008-02': 937.3, '2008-03': 991.7, '2008-04': 999.7, '2008-05': 1031.4, '2008-06': 1043.4, '2008-07': 1008.5, '2008-08': 1081.8, '2008-09': 1187.7, '2008-10': 1291.4, '2008-11': 1482.7, '2008-12': 1257.5, '2009-01': 1368.5, '2009-02': 1516.4, '2009-03': 1377.1, '2009-04': 1348.0, '2009-05': 1272.9, '2009-06': 1284.7, '2009-07': 1240.5, '2009-08': 1244.9, '2009-09': 1188.7, '2009-10': 1200.6, '2009-11': 1167.4, '2009-12': 1167.6, '2010-01': 1156.5, '2010-02': 1158.4, '2010-03': 1130.8, '2010-04': 1115.5, '2010-05': 1200.2, '2010-06': 1210.3, '2010-07': 1187.2, '2010-08': 1189.1, '2010-09': 1142.0, '2010-10': 1126.6, '2010-11': 1157.3, '2010-12': 1138.9, '2011-01': 1114.3, '2011-02': 1127.9, '2011-03': 1107.2, '2011-04': 1072.3, '2011-05': 1080.6, '2011-06': 1078.1, '2011-07': 1052.6, '2011-08': 1071.7, '2011-09': 1179.5, '2011-10': 1104.5, '2011-11': 1150.3, '2011-12': 1153.3, '2012-01': 1125.0, '2012-02': 1126.5, '2012-03': 1137.8, '2012-04': 1134.2, '2012-05': 1177.8, '2012-06': 1153.8, '2012-07': 1136.2, '2012-08': 1134.6, '2012-09': 1118.6, '2012-10': 1094.1, '2012-11': 1084.7, '2012-12': 1071.1, '2013-01': 1082.7, '2013-02': 1085.4, '2013-03': 1112.1, '2013-04': 1108.1, '2013-05': 1128.3, '2013-06': 1149.7, '2013-07': 1113.6, '2013-08': 1110.9, '2013-09': 1075.6, '2013-10': 1061.4, '2013-11': 1062.1, '2013-12': 1055.3, '2014-01': 1079.2, '2014-02': 1067.7, '2014-03': 1068.8, '2014-04': 1031.7, '2014-05': 1021.6, '2014-06': 1014.4, '2014-07': 1024.3, '2014-08': 1013.6, '2014-09': 1050.6, '2014-10': 1054.0, '2014-11': 1101.1, '2014-12': 1099.2, '2015-01': 1090.8, '2015-02': 1099.2, '2015-03': 1105.0, '2015-04': 1068.1, '2015-05': 1108.0, '2015-06': 1124.1, '2015-07': 1166.3, '2015-08': 1176.3, '2015-09': 1194.5, '2015-10': 1142.3, '2015-11': 1150.4, '2015-12': 1172.0, '2016-01': 1208.4, '2016-02': 1235.4, '2016-03': 1153.5, '2016-04': 1143.9, '2016-05': 1190.6, '2016-06': 1164.7, '2016-07': 1125.7, '2016-08': 1118.5, '2016-09': 1096.3, '2016-10': 1145.2, '2016-11': 1168.5, '2016-12': 1208.5, '2017-01': 1157.8, '2017-02': 1132.1, '2017-03': 1116.1, '2017-04': 1130.1, '2017-05': 1123.9, '2017-06': 1139.6, '2017-07': 1119.1, '2017-08': 1122.8, '2017-09': 1146.7, '2017-10': 1125.0, '2017-11': 1082.4, '2017-12': 1071.4, '2018-01': 1071.5, '2018-02': 1071.0, '2018-03': 1066.5, '2018-04': 1076.2, '2018-05': 1081.3, '2018-06': 1121.7, '2018-07': 1116.7, '2018-08': 1108.8, '2018-09': 1112.7, '2018-10': 1140.6, '2018-11': 1121.8, '2018-12': 1118.1, '2019-01': 1117.2, '2019-02': 1117.8, '2019-03': 1137.8, '2019-04': 1158.2, '2019-05': 1190.0, '2019-06': 1156.8, '2019-07': 1182.0, '2019-08': 1215.2, '2019-09': 1201.3, '2019-10': 1168.4, '2019-11': 1179.3, '2019-12': 1157.8, '2020-01': 1183.5, '2020-02': 1215.9, '2020-03': 1222.6, '2020-04': 1225.2, '2020-05': 1239.4, '2020-06': 1200.7, '2020-07': 1191.4, '2020-08': 1185.1, '2020-09': 1173.5, '2020-10': 1133.4, '2020-11': 1104.4, '2020-12': 1088.0, '2021-01': 1114.6, '2021-02': 1108.4, '2021-03': 1133.5, '2021-04': 1107.4, '2021-05': 1116.0, '2021-06': 1130.0, '2021-07': 1147.4, '2021-08': 1164.4, '2021-09': 1184.9, '2021-10': 1171.7, '2021-11': 1193.4, '2021-12': 1185.5, '2022-01': 1202.4, '2022-02': 1202.7, '2022-03': 1210.8, '2022-04': 1269.4, '2022-05': 1245.8, '2022-06': 1292.9, '2022-07': 1304.0, '2022-08': 1347.5, '2022-09': 1434.8, '2022-10': 1419.3, '2022-11': 1331.5, '2022-12': 1267.3, '2023-01': 1228.7, '2023-02': 1317.4, '2023-03': 1303.8, '2023-04': 1339.9, '2023-05': 1322.2, '2023-06': 1312.8, '2023-07': 1280.0, '2023-08': 1321.4, '2023-09': 1344.8, '2023-10': 1352.8, '2023-11': 1289.0, '2023-12': 1289.4, '2024-01': 1330.6, '2024-02': 1334.0, '2024-03': 1346.8, '2024-04': 1378.7, '2024-05': 1376.5, '2024-06': 1389.2, '2024-07': 1384.6, '2024-08': 1335.3, '2024-09': 1319.6, '2024-10': 1383.3, '2024-11': 1394.7, '2024-12': 1470.0, '2025-01': 1433.3, '2025-02': 1439.6, '2025-03': 1466.5, '2025-04': 1438.5, '2025-05': 1381.4, '2025-06': 1356.4, '2025-07': 1382.9, '2025-08': 1388.6, '2025-09': 1402.2, '2025-10': 1423.2, '2025-11': 1464.8, '2025-12': 1434.9, '2026-01': 1427.0, '2026-02': 1424.5, '2026-03': 1513.4, '2026-04': 1476.1, '2026-05': 1505.8, '2026-06': 1541.5, '2026-07': 1441.1, '2026-08': 1376.5, '2026-09': 1358.4}

def ecos_fx_rates(months):
    """한국은행 ECOS 원/미국달러 매매기준율 말일자료 (내장 CSV 스냅샷)."""
    rates = []
    for m in months:
        current = ECOS_FX.get(m.strftime("%Y-%m"))
        previous = ECOS_FX.get((m - pd.DateOffset(months=1)).strftime("%Y-%m"))
        rates.append((current / previous - 1) * 100
                     if current is not None and previous is not None and previous > 0 else None)
    return rates

def get_one(ticker, months):
    first = min(months) - pd.DateOffset(months=1)
    last = max(months) + pd.DateOffset(months=1)
    start, end = first.strftime("%Y-%m-%d"), last.strftime("%Y-%m-%d")
    if ticker == "KRW=X":
        try:
            return ticker, ecos_fx_rates(months), "한국은행 ECOS 원/미국달러 매매기준율 말일자료 (1998-01~2026-09)"
        except Exception as e:
            return ticker, [None]*len(months), f"ECOS 데이터 처리 실패: {str(e)[:70]}"
    if ticker == "^KS200":
        try:
            import FinanceDataReader as fdr
            df = fdr.DataReader("KS200", start, end)
            return ticker, monthly_rates(df, months), "FinanceDataReader KS200"
        except Exception as e:
            return ticker, [None]*len(months), f"KS200 조회 실패: {str(e)[:70]}"
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
        return ticker, [None]*len(months), f"조회 실패: {str(e)[:70]}"

@st.cache_data(ttl=3600, show_spinner=False)
def fetch(year, month):
    months = [pd.Timestamp(year, month, 1) + pd.DateOffset(months=i) for i in range(6)]
    display_months = months + [months[0] - pd.DateOffset(months=1)]
    results = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = {pool.submit(get_one, ticker, display_months): ticker for ticker, _ in ALL}
        for job in as_completed(jobs):
            ticker = jobs[job]
            try:
                _, values, note = job.result()
            except Exception as e:
                values, note = [None]*7, f"조회 실패: {str(e)[:70]}"
            results[ticker] = (values, note)
    return display_months, results

st.title("📈 월간 주식 등락률")
st.caption("기본 21개 고정 · 나머지 131개 선택 월 등락률순 · 6개월 + 전월 비교 · 금 상/하 기록 표시")

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
    rows = [(ticker, name, *values.get(ticker, ([None]*7, "데이터 없음")))
            for ticker, name in ALL]
    selected = lambda row: row[2][0]
    ordered = rows[:len(BASE)] + sorted(rows[len(BASE):], key=lambda r: (
        selected(r) is None, -(selected(r) if selected(r) is not None else 0)))
    available = sum(selected(r) is not None for r in ordered)
    st.caption(f"{yy}년 {mm}월 기준 · {len(ordered)}개 종목 중 {available}개 수익률 조회")
    st.caption("기본 21개는 고정, 추가 131개만 월 제목 클릭 시 정렬됩니다. 마지막 열은 전월 수익률입니다.")
    style = """
    <style>
    body{margin:0;font-family:system-ui,-apple-system,sans-serif}
    .asset-scroll{width:100%;height:650px;overflow:auto;border:1px solid #ddd;border-radius:8px}
    .asset-table{border-collapse:separate;border-spacing:0;min-width:760px;width:max-content;font-size:12px;line-height:1.35}
    .asset-table th,.asset-table td{padding:9px 6px;border-bottom:1px solid rgba(100,100,100,.12);white-space:nowrap;text-align:right}
    .asset-table th{background:#f0f1f4;color:#222;position:sticky;top:0;z-index:3;cursor:pointer;user-select:none}
    .asset-table th:hover{background:#dbe4f3}
    .asset-table .ticker{position:sticky;left:0;text-align:left;min-width:74px;width:74px;max-width:74px;z-index:2;font-weight:600}
    .asset-table .name{position:sticky;left:74px;text-align:left;min-width:104px;width:104px;max-width:104px;overflow:hidden;text-overflow:ellipsis;z-index:2}
    .asset-table th.ticker,.asset-table th.name{z-index:4;background:#f0f1f4}
    .asset-table td.month{min-width:77px;width:77px;font-variant-numeric:tabular-nums;font-weight:650}
    .asset-table .up{color:#c62828}.asset-table .down{color:#1565c0}.asset-table .zero{color:#555}
    .fx-price{display:block;margin-top:3px;font-size:11px;font-weight:500;color:#555;white-space:nowrap}
    .gold-tag{margin-left:3px;font-size:11px;font-weight:700}
    .gold-tag.gold-up{color:#c62828}.gold-tag.gold-down{color:#1565c0}.gold-tag.gold-missing{color:#888}
    .asset-table tr.positive td{background:#fff0f0}.asset-table tr.negative td{background:#edf4ff}
    .asset-table tr.neutral td{background:#f6f6f6}
    .asset-table th.selected{background:#d7e1f0}
    .hint{font-size:11px;color:#777;padding:4px 0 7px}
    </style>
    """
    headers = ''.join(
        f'<th class="{ "selected" if i == 0 else ""}" onclick="sortByMonth({i})" data-month="{i}">'
        f'{m.year}년 {m.month}월 {"▼" if i == 0 else "↕"}</th>'
        for i, m in enumerate(months))
    html_rows = []
    for ticker, name, rates, note in ordered:
        base = rates[0]
        row_class = "neutral" if base is None or base == 0 else ("positive" if base > 0 else "negative")
        cells = []
        for idx, rate in enumerate(rates):
            cl = "zero" if rate is None or rate == 0 else ("up" if rate > 0 else "down")
            value = "—" if rate is None else f"{rate:+.1f}%"
            gold_html = ""
            fx_title = ""
            fx_html = ""
            if ticker == "KRW=X":
                fx_price = ECOS_FX.get(months[idx].strftime("%Y-%m"))
                if fx_price is not None:
                    fx_title = f' title="월말 환율: {fx_price:,.2f}원 (한국은행 ECOS)"'
                    fx_html = f'<span class="fx-price">{fx_price:,.2f}원</span>'
            if ticker == "GLD":
                status = gold_month_status(months[idx])
                status_class = {"상": "gold-up", "하": "gold-down", "미": "gold-missing"}[status]
                gold_html = f'<span class="gold-tag {status_class}">({status})</span>'
            cells.append(f'<td class="month {cl}"{fx_title}>{value}{gold_html}{fx_html}</td>')
        data = ','.join('null' if rate is None else str(round(rate, 8)) for rate in rates)
        html_rows.append(
            f'<tr class="{row_class}" data-rates="[{data}]"><td class="ticker">{html.escape(ticker)}</td>'
            f'<td class="name" title="{html.escape(name, quote=True)}">{html.escape(name)}</td>'
            + ''.join(cells) + '</tr>')
    javascript = """
    <script>
    const tbody = document.querySelector('#assets tbody');
    const original = Array.from(tbody.rows);
    const fixedRows = original.slice(0, 21); // 기본 21개는 언제나 원래 순서 유지
    let currentCol = -1;
    let descending = true;
    function sortByMonth(col) {
      if (currentCol === col) descending = !descending;
      else { currentCol = col; descending = true; }
      const rows = Array.from(tbody.rows).filter(row => !fixedRows.includes(row));
      rows.sort((a,b) => {
        const x = JSON.parse(a.dataset.rates)[col];
        const y = JSON.parse(b.dataset.rates)[col];
        if (x === null && y === null) return original.indexOf(a)-original.indexOf(b);
        if (x === null) return 1;
        if (y === null) return -1;
        return descending ? y-x : x-y;
      });
      tbody.replaceChildren(...fixedRows, ...rows);
      document.querySelectorAll('th[data-month]').forEach(h => {
        const i = Number(h.dataset.month);
        const d = h.textContent.replace(/[▼▲↕]/g,'').trim();
        h.textContent = d + (i === col ? (descending ? ' ▼' : ' ▲') : ' ↕');
        h.classList.toggle('selected',i === col);
      });
    }
    </script>
    """
    components.html(
        style + '<div class="hint">월 제목을 누르면 추가 131개만 내림차순 / 오름차순으로 바뀝니다.</div>'
        + '<div class="asset-scroll"><table id="assets" class="asset-table"><thead><tr>'
        '<th class="ticker">티커</th><th class="name">종목명</th>'
        + headers + '</tr></thead><tbody>' + ''.join(html_rows)
        + '</tbody></table></div>' + javascript,
        height=690, scrolling=False
    )
    fx = values.get("KRW=X", ([None]*7, "조회 실패"))
    st.caption("달러/원: " + fx[1])
    missing = [(ticker, note) for ticker, _, rates, note in ordered if rates[0] is None]
    if missing:
        with st.expander(f"선택 월 미조회 종목 ({len(missing)}개)"):
            for ticker, note in missing:
                st.text(f"{ticker}: {note if note != 'Yahoo Finance' else '상장 전 또는 데이터 없음'}")
    columns = [f"{m.year}-{m.month:02d} 등락률(%)" for m in months]
    export = pd.DataFrame([{"티커":ticker, "종목명":name,
                            **{columns[i]: rates[i] for i in range(len(months))},
                            "전월 등락률(%)": rates[6],
                            **({**{f"{months[i].year}-{months[i].month:02d} 금 기록": gold_month_status(months[i]) for i in range(len(months))},
                                "전월 금 기록": gold_month_status(months[6])} if ticker == "GLD" else {}),
                            **({f"{months[i].year}-{months[i].month:02d} 월말 환율(원)": ECOS_FX.get(months[i].strftime("%Y-%m")) for i in range(len(months))} if ticker == "KRW=X" else {}),
                            "데이터 출처":note}
                           for ticker, name, rates, note in ordered])
    st.download_button("6개월 + 전월 CSV 다운로드", export.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"monthly_{yy}_{mm:02d}_6months_plus_previous.csv",
                       mime="text/csv", use_container_width=True)

st.caption("선택 연월은 웹주소에 저장됩니다. 그 주소를 즐겨찾기하면 다음 방문에도 같은 연월로 열립니다.")
st.caption("달러/원: 한국은행 ECOS 월말 매매기준율 (2026-09까지 내장) · 코스피200: FinanceDataReader KS200 · 금: GLD ETF(달러 기준)")
