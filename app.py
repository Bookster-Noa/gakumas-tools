# app.py (最小のStreamlitサンプル)

import streamlit as st

def main():
    st.title("SPレッスン確率計算アプリ (2極編成)")

    st.header("【1】Xレッスン/Yレッスンを選択")
    st.write("ボーカル・ダンス・ビジュアルの3種類から、使う2種類を選んでください。")

    lessons = ["ボーカル", "ダンス", "ビジュアル"]
    chosen = st.multiselect(
        "2つ選択 (重複不可)",
        lessons,
        default=["ダンス", "ビジュアル"]  # デフォルト例
    )
    if len(chosen) != 2:
        st.error("※2つ選んでください。")
        return

    x_label, y_label = chosen[0], chosen[1]

    st.write("---")

    st.header("【2】SP率増加値を入力 (基礎10%)")

    # XレッスンSPアップ率 (整数％)
    x_up_percent = st.number_input(
        f"{x_label} SPレッスン発生率増加(％)",
        min_value=0, max_value=100, value=50, step=1
    )
    # 内部計算 (0.10 + x_up_percent/100)
    pX = min(0.10 + x_up_percent / 100.0, 1.0)

    # YレッスンSPアップ率 (整数％)
    y_up_percent = st.number_input(
        f"{y_label} SPレッスン発生率増加(％)",
        min_value=0, max_value=100, value=50, step=1
    )
    pY = min(0.10 + y_up_percent / 100.0, 1.0)

    st.write("---")

    st.header(f"【3】{x_label}SPの目標回数 (全8ターン)")
    target_x = st.slider(
        f"{x_label} を最終的に何回SPにしたい？",
        0, 8, 4
    )

    st.write("---")

    # -----------------------------
    # ここで pX_only, pY_only, pBoth, pNone を定義（どのボタンでも使えるように）
    # -----------------------------
    pX_only = pX * (1 - pY)
    pY_only = (1 - pX) * pY
    pBoth   = pX * pY
    pNone   = (1 - pX) * (1 - pY)

    # 1ターンあたり「少なくともどちらかがSP」 => pX + pY - pX*pY
    pAtLeastOne = pX + pY - pX*pY
    # 8ターン連続で「少なくとも片方がSP」 => (pAtLeastOne)^8
    prob_both_sp_8 = (pAtLeastOne) ** 8

    # DP用の関数を定義
    TOTAL_TURNS = 8

    memo_main = {}
    def success_probability(i, x_count):
        """ 
        i: 何ターン目(0〜8)
        x_count: ここまでXレッスンSPを選んだ回数
        戻り値:
          8ターン連続SP & Xが最終的に target_x 回になる最大確率
        """
        if i == TOTAL_TURNS:
            return 1.0 if (x_count == target_x) else 0.0
        if (i, x_count) in memo_main:
            return memo_main[(i, x_count)]

        # 1) XのみSP
        prob_xonly = success_probability(i+1, x_count+1)
        # 2) YのみSP
        prob_yonly = success_probability(i+1, x_count)
        # 3) 両方SP => 好きに選べる(成功確率が高い方)
        prob_choose_x = success_probability(i+1, x_count+1)
        prob_choose_y = success_probability(i+1, x_count)
        best_both = max(prob_choose_x, prob_choose_y)
        # 4) どちらもSPでない => 0
        prob_none = 0.0

        ans = (
            pX_only * prob_xonly +
            pY_only * prob_yonly +
            pBoth   * best_both +
            pNone   * prob_none
        )
        memo_main[(i, x_count)] = ans
        return ans

    # 「計算する」ボタン
    if st.button("計算する"):
        final_prob = success_probability(0, 0)

        st.subheader("【計算結果】")

        x_rate_percent = int(pX * 100)
        y_rate_percent = int(pY * 100)
        st.write(f"{x_label} SP率: {x_rate_percent}%,   {y_label} SP率: {y_rate_percent}%")

        # 8ターン連続で少なくとも片方SPになる確率
        st.write(f"・8ターン全部で少なくともどちらかSPになる確率: **{prob_both_sp_8*100:.3f}%**")

        st.write(f"・{x_label}SPを {target_x}回、{y_label}SPを {8 - target_x}回踏みたい場合:")
        st.write(f"  成功確率: **{final_prob*100:.3f}%**")

    st.write("---")

    # (C) 途中経過用の2つ目のDP
    st.subheader(f"【4】(任意) 次ターン両方SPの場合 {x_label} or {y_label} どちらを踏むべきか")

    i_now = st.number_input("経過ターン数 (0〜8)", min_value=0, max_value=8, value=0)
    x_now = st.number_input(f"現在 {x_label} SPを踏んだ回数(0〜8)", min_value=0, max_value=8, value=0)

    memo_sub = {}
    def success_prob_sub(i, x_count):
        if i == TOTAL_TURNS:
            return 1.0 if (x_count == target_x) else 0.0
        if (i, x_count) in memo_sub:
            return memo_sub[(i, x_count)]

        pr_xonly = success_prob_sub(i+1, x_count+1)
        pr_yonly = success_prob_sub(i+1, x_count)
        pr_choose_x = success_prob_sub(i+1, x_count+1)
        pr_choose_y = success_prob_sub(i+1, x_count)
        best_both = max(pr_choose_x, pr_choose_y)
        pr_none = 0.0

        ans2 = (pX_only * pr_xonly
                + pY_only * pr_yonly
                + pBoth   * best_both
                + pNone   * pr_none)
        memo_sub[(i, x_count)] = ans2
        return ans2

    if st.button("判定する"):
        prob_x = success_prob_sub(i_now+1, x_now+1)
        prob_y = success_prob_sub(i_now+1, x_now)

        st.write(f"現在 {i_now}ターン経過で、{x_label} SP {x_now}回")
        st.write("次のターンが両方SPの場合、")
        st.write(f"  - {x_label}を踏む => 成功確率: {prob_x*100:.3f}%")
        st.write(f"  - {y_label}を踏む => 成功確率: {prob_y*100:.3f}%")

        if prob_x > prob_y:
            st.write(f"⇒ **{x_label} を踏むほうが成功確率が高い**です。")
        elif prob_x < prob_y:
            st.write(f"⇒ **{y_label} を踏む踏むほうが成功確率が高い**です。")
        else:
            st.write("⇒ **どちらを踏んでも同じ成功確率**です。")


if __name__ == "__main__":
    main()
