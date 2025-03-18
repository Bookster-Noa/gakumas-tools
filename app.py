import streamlit as st
from functools import lru_cache

st.set_page_config(page_title="SP発生確率計算ツール", layout="centered")

def main():
    st.write("## SP発生確率計算ツール")
    st.write("""
NIA編における全8週のレッスンを数理的にシミュレーションし、最適な戦略の策定をサポートします。  
ご自身のアイドルと相談しながら条件を設定してください。  
※サポカ編成提案ツールも開発中です
""")
    
    st.markdown("---")
    # 1) SP発生率入力
    st.write("### 各種SPレッスン発生率増加値")
    st.write("""
育成中にP手帳の編成から確認できます。  
基礎値10%にユーザーが入力した値を加算してSP発生率とします。  
(0〜100、0.5刻み)
""")
    vocal_up  = st.number_input("ボーカル(％)", 0.0, 100.0, 0.0, 0.5, format="%.1f")
    dance_up  = st.number_input("ダンス(％)",   0.0, 100.0, 0.0, 0.5, format="%.1f")
    visual_up = st.number_input("ビジュアル(％)", 0.0, 100.0, 0.0, 0.5, format="%.1f")

    pV = min(0.10 + vocal_up/100.0, 1.0)
    pD = min(0.10 + dance_up/100.0, 1.0)
    pB = min(0.10 + visual_up/100.0, 1.0)
    
    st.write(f"最終SP発生率: ボーカル {pV*100:.1f}%, ダンス {pD*100:.1f}%, ビジュアル {pB*100:.1f}%")
    
    st.markdown("---")
    # 2) 最低条件
    st.write("### 最低条件")
    st.write("各種最低でも何回SPを踏みたいか(合計0〜8回)")
    min_v = st.number_input("ボーカル最低回数", 0, 8, 0)
    min_d = st.number_input("ダンス最低回数",   0, 8, 0)
    min_b = st.number_input("ビジュアル最低回数", 0, 8, 0)
    sum_min = min_v + min_d + min_b
    st.write(f"現在の最低条件合計: {sum_min} 回")
    if sum_min > 8:
        st.error("最低条件の合計が8回を超えています。")

    st.markdown("---")
    # 3) 理想条件
    st.write("### 理想条件")
    st.write("各種理想で何回SPを踏みたいか (合計8回)")
    ideal_v = st.number_input("ボーカル理想回数", 0, 8, 0)
    ideal_d = st.number_input("ダンス理想回数",   0, 8, 0)
    ideal_b = st.number_input("ビジュアル理想回数", 0, 8, 0)
    sum_ideal = ideal_v + ideal_d + ideal_b
    if sum_ideal not in (0, 8):
        st.error("理想条件の合計は8回、もしくは未設定(0)にしてください。")

    st.markdown("---")
    if st.button("計算する"):
        if sum_min > 8:
            st.error("最低条件の合計が8回を超えています。修正してください。")
        elif sum_min == 0 and sum_ideal == 0:
            st.error("最低条件 または 理想条件のどちらかは設定してください。")
        else:
            dp_clear_cache()
            # dp(0,0,0,0) の戻り値 => (minC, minAndAll, idealC, allSP)
            res = dp(0, 0, 0, 0, pV, pD, pB, min_v, min_d, min_b,
                     ideal_v, ideal_d, ideal_b, sum_ideal)
            
            st.write("#### 計算結果")
            st.write(f"- 最低条件(Vo≥{min_v}, Da≥{min_d}, Vi≥{min_b})達成確率: **{res[0]*100:.3f}%**")
            st.write(f"- 最低条件達成＋全8回SPの確率: **{res[1]*100:.3f}%**")
            if sum_ideal == 8:
                st.write(f"- 理想条件(Vo={ideal_v}, Da={ideal_d}, Vi={ideal_b})達成確率: **{res[2]*100:.3f}%**")
            else:
                st.write("- 理想条件: 未設定")
            st.write(f"- 全8回SPの確率: **{res[3]*100:.3f}%**")

    st.markdown("---")
    # --- SP選択提案 ---
    st.write("### SP選択の提案")
    st.write("""
次のターンで複数のSPレッスンが発生した場合、状況と条件を考慮してどれを踏むと最終的に条件達成確率が高くなるかを提案します。
""")
    i_now = st.number_input("現在の経過ターン数 (0〜7)", 0, 7, 0)
    st.write("これまでに踏んだSP回数")
    curr_v = st.number_input("ボーカルSP回数", 0, 7, 0)
    curr_d = st.number_input("ダンスSP回数",   0, 7, 0)
    curr_b = st.number_input("ビジュアルSP回数", 0, 7, 0)

    if st.button("判定する"):
        if curr_v + curr_d + curr_b > i_now:
            st.error("経過ターン数より合計SP回数が多くなっています。")
        else:
            dp_clear_cache()
            pickV = dp(i_now+1, curr_v+1, curr_d, curr_b, pV, pD, pB,
                       min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
            pickD = dp(i_now+1, curr_v, curr_d+1, curr_b, pV, pD, pB,
                       min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
            pickB = dp(i_now+1, curr_v, curr_d, curr_b+1, pV, pD, pB,
                       min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)

            def bold_if_best(name, val, best):
                return f"**{name}**" if abs(val - best) < 1e-12 else name

            # 最低条件達成確率の評価
            minV, minD_, minB_ = pickV[0], pickD[0], pickB[0]
            best_min = max(minV, minD_, minB_)
            v_lbl_min = bold_if_best("ボーカル", minV, best_min)
            d_lbl_min = bold_if_best("ダンス",   minD_, best_min)
            b_lbl_min = bold_if_best("ビジュアル", minB_, best_min)

            # 理想条件達成確率の評価
            idealV, idealD_, idealB_ = pickV[2], pickD[2], pickB[2]
            best_ideal = max(idealV, idealD_, idealB_)
            v_lbl_ideal = bold_if_best("ボーカル", idealV, best_ideal)
            d_lbl_ideal = bold_if_best("ダンス",   idealD_, best_ideal)
            b_lbl_ideal = bold_if_best("ビジュアル", idealB_, best_ideal)

            st.write("#### 次ターン各SP選択時の比較")
            st.write("【最低条件達成確率】")
            st.write(f"- {v_lbl_min}: {minV*100:.3f}%")
            st.write(f"- {d_lbl_min}: {minD_*100:.3f}%")
            st.write(f"- {b_lbl_min}: {minB_*100:.3f}%")

            st.write("【理想条件達成確率】")
            st.write(f"- {v_lbl_ideal}: {idealV*100:.3f}%")
            st.write(f"- {d_lbl_ideal}: {idealD_*100:.3f}%")
            st.write(f"- {b_lbl_ideal}: {idealB_*100:.3f}%")

@lru_cache(None)
def dp(i, v, d, b,
       pV, pD, pB,
       min_v, min_d, min_b,
       ideal_v, ideal_d, ideal_b,
       sum_ideal):
    """
    dp(i,v,d,b) の戻り値: (minC, minAndAll, idealC, allSP)
    - iターン目(0〜8)で、既にボーカルSP=v, ダンスSP=d, ビジュアルSP=b 取得済み
    - 残り(8-i)ターンで、最適に選択した場合の達成確率を計算
      * minC: 最低条件達成確率 (Vo≥min_v, Da≥min_d, Vi≥min_b)
      * minAndAll: 上記に加え、全レッスンでSP (v+d+b=8)となる確率
      * idealC: 理想条件 (sum_ideal==8の場合、Vo==ideal_v, Da==ideal_d, Vi==ideal_b) 達成確率
      * allSP: 全レッスンでSP (v+d+b==8) となる確率
    """

    if i == 8:
        minCond = 1.0 if (v >= min_v and d >= min_d and b >= min_b) else 0.0
        minAndAll = 1.0 if (minCond > 0 and (v+d+b) == 8) else 0.0
        idealCond = 1.0 if (sum_ideal == 8 and v == ideal_v and d == ideal_d and b == ideal_b) else 0.0
        allsp = 1.0 if (v+d+b) == 8 else 0.0
        return (minCond, minAndAll, idealCond, allsp)

    # 各確率の計算
    p_vonly = pV * (1 - pD) * (1 - pB)
    p_donly = (1 - pV) * pD * (1 - pB)
    p_bonly = (1 - pV) * (1 - pD) * pB
    p_vd    = pV * pD * (1 - pB)
    p_vb    = pV * (1 - pD) * pB
    p_db    = (1 - pV) * pD * pB
    p_vdb   = pV * pD * pB
    p_none  = 1.0 - (p_vonly + p_donly + p_bonly + p_vd + p_vb + p_db + p_vdb)
    if p_none < 0:
        p_none = 0.0

    minC = 0.0
    minAll = 0.0
    idealC = 0.0
    allsp = 0.0

    # 1) none (SP無し)
    r_none = dp(i+1, v, d, b, pV, pD, pB,
                min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
    minC   += p_none * r_none[0]
    minAll += p_none * r_none[1]
    idealC += p_none * r_none[2]
    allsp  += p_none * r_none[3]

    # 2) ボーカルのみ
    r_vonly = dp(i+1, v+1, d, b, pV, pD, pB,
                 min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
    minC   += p_vonly * r_vonly[0]
    minAll += p_vonly * r_vonly[1]
    idealC += p_vonly * r_vonly[2]
    allsp  += p_vonly * r_vonly[3]

    # 3) ダンスのみ
    r_donly = dp(i+1, v, d+1, b, pV, pD, pB,
                 min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
    minC   += p_donly * r_donly[0]
    minAll += p_donly * r_donly[1]
    idealC += p_donly * r_donly[2]
    allsp  += p_donly * r_donly[3]

    # 4) ビジュアルのみ
    r_bonly = dp(i+1, v, d, b+1, pV, pD, pB,
                 min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
    minC   += p_bonly * r_bonly[0]
    minAll += p_bonly * r_bonly[1]
    idealC += p_bonly * r_bonly[2]
    allsp  += p_bonly * r_bonly[3]

    # 5) ボーカル＋ダンス
    cand_v = dp(i+1, v+1, d, b, pV, pD, pB,
                min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
    cand_d = dp(i+1, v, d+1, b, pV, pD, pB,
                min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
    best_vd = max_tuple(cand_v, cand_d)
    minC   += p_vd * best_vd[0]
    minAll += p_vd * best_vd[1]
    idealC += p_vd * best_vd[2]
    allsp  += p_vd * best_vd[3]

    # 6) ボーカル＋ビジュアル
    cand_v = dp(i+1, v+1, d, b, pV, pD, pB,
                min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
    cand_b = dp(i+1, v, d, b+1, pV, pD, pB,
                min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
    best_vb = max_tuple(cand_v, cand_b)
    minC   += p_vb * best_vb[0]
    minAll += p_vb * best_vb[1]
    idealC += p_vb * best_vb[2]
    allsp  += p_vb * best_vb[3]

    # 7) ダンス＋ビジュアル
    cand_d = dp(i+1, v, d+1, b, pV, pD, pB,
                min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
    cand_b = dp(i+1, v, d, b+1, pV, pD, pB,
                min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
    best_db = max_tuple(cand_d, cand_b)
    minC   += p_db * best_db[0]
    minAll += p_db * best_db[1]
    idealC += p_db * best_db[2]
    allsp  += p_db * best_db[3]

    # 8) 3種SP (ボーカル＋ダンス＋ビジュアル)
    cand_v = dp(i+1, v+1, d, b, pV, pD, pB,
                min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
    cand_d = dp(i+1, v, d+1, b, pV, pD, pB,
                min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
    cand_b_ = dp(i+1, v, d, b+1, pV, pD, pB,
                 min_v, min_d, min_b, ideal_v, ideal_d, ideal_b, sum_ideal)
    best_vdb = max_tuple(cand_v, cand_d, cand_b_)
    minC   += p_vdb * best_vdb[0]
    minAll += p_vdb * best_vdb[1]
    idealC += p_vdb * best_vdb[2]
    allsp  += p_vdb * best_vdb[3]

    return (minC, minAll, idealC, allsp)

def max_tuple(*args):
    # 基準は「minC + idealC + allsp」をスコアにして比較
    def score(t): 
        return t[0] + t[2] + t[3]
    best = None
    best_val = -1.0
    for tp in args:
        val = score(tp)
        if val > best_val:
            best = tp
            best_val = val
    return best

def dp_clear_cache():
    dp.cache_clear()

if __name__ == "__main__":
    main()
