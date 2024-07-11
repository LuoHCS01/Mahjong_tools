from utils import *
import os
import pandas as pd
import numpy as np
import plotly
import plotly.express as px

# 获取所有半庄对局
def get_all_games():
    filenames = os.listdir("./data")
    filenames.remove("nickname_list.json")
    games = []
    for filename in filenames:
        game = load(f"data/{filename}")
        if game["游戏类型"] == "半庄":
            games.append(game)
    return games

# 获取所有玩家
def get_all_players(games):
    players = []
    for game in games:
        for player in game["玩家"].values():
            if player not in players:
                players.append(player)
    return players

# 获取详细数据表格，其中部分数据解析：
#   打点效率：胡牌率 * 平均打点
#   铳点损失：放铳率 * 平均铳点
#   净打点：打点效率 - 铳点损失
#   被炸率：坐庄时被自摸7900+
#   被炸点：被炸庄时别家平均自摸打点
#   悬赏牌：胡牌时平均宝牌数量
def detailed_stats(games, players):
    data_index = [
        "总场数", "总局数", "总得点", "素点", "一位率", "二位率", "三位率", "四位率", "被飞率", "平均顺位", "最高点数",
        "胡牌率", "自摸率", "放铳率", "立直率", "立直胡率", "立直铳率", "平均打点", "立直打点", "平均铳点",
        "打点效率", "铳点损失", "净打点", "被炸率", "被炸点", "局收支", "悬赏牌", "中里率", "里2数", "里3+数", "一发率"
    ]
    stat_df = pd.DataFrame(0.0, index=data_index, columns=players)
    data_index = [
        "局数", "胡牌数", "自摸数", "放铳数", "立直数", "立直胡牌数", "立直放铳数", "总打点", "立直打点", "总铳点",
        "坐庄数", "被炸数", "被炸点", "表宝牌数", "赤宝牌数", "里宝牌数", "中里次数", "里2数", "里3+数", "一发数"
    ]
    stat_aux = pd.DataFrame(0.0, index=data_index, columns=players)

    # 统计总得点及位次
    #   半庄战马点默认按M规计：+50, +10, -10, -30
    #   同分默认按座次排序
    reward = [50, 10, -10, -30]
    stat_df.loc["最高点数"] = -1e9
    for game in games:
        final_points = sorted(game["最终点数"].items(), key=lambda x: x[1], reverse=True)
        for i in range(4):
            player, point = final_points[i]
            stat_df[player]["总场数"] += 1
            stat_df[player]["总得点"] += point * 0.001 - 30 + reward[i]
            stat_df[player]["素点"] += point * 0.001 - 25
            index_list = ["一位率", "二位率", "三位率", "四位率"]
            stat_df[player][index_list[i]] += 1
            if point < 0:
                stat_df[player]["被飞率"] += 1
            stat_df[player]["最高点数"] = max(stat_df[player]["最高点数"], point)
    for row in ["一位率", "二位率", "三位率", "四位率", "被飞率"]:
        stat_df.loc[row] /= (stat_df.loc["总场数"] + 1e-15)
    stat_df.loc["平均顺位"] = stat_df.loc["一位率"] * 1 + stat_df.loc["二位率"] * 2 + stat_df.loc["三位率"] * 3 + stat_df.loc["四位率"] * 4

    # 统计其他数据
    for game in games:
        for one_round in game["对局结果"]:
            dealer = list(game["玩家"].values())[int(one_round["场次"][1]) - 1]
            stat_aux[dealer]["坐庄数"] += 1
            for player in game["玩家"].values():
                stat_aux[player]["局数"] += 1
            for player in one_round["立直家"]:
                stat_aux[player]["立直数"] += 1
            for win in one_round["胡牌"]:
                win_player = win["胡牌者"]
                fire_player = win["放铳者"]
                if win_player in one_round["立直家"]:
                    stat_aux[win_player]["立直胡牌数"] += 1
                    stat_aux[win_player]["立直打点"] += win["打点"]
                if fire_player in one_round["立直家"]:
                    stat_aux[fire_player]["立直放铳数"] += 1
                stat_aux[win_player]["胡牌数"] += 1
                stat_aux[win_player]["总打点"] += win["打点"]
                if win["是否自摸"] == "是":
                    stat_aux[win_player]["自摸数"] += 1
                    if (win["打点"] >= 7900) and (dealer != win["胡牌者"]):
                        stat_aux[dealer]["被炸数"] += 1
                        stat_aux[dealer]["被炸点"] += win["打点"]
                else:
                    stat_aux[fire_player]["放铳数"] += 1
                    stat_aux[fire_player]["总铳点"] += win["打点"]
                stat_aux[win_player]["表宝牌数"] += win["Dora"]
                stat_aux[win_player]["赤宝牌数"] += win["Aka"]
                stat_aux[win_player]["里宝牌数"] += win["Ura"]
                if win["Ura"] > 0:
                    stat_aux[win_player]["中里次数"] += 1
                if win["Ura"] == 2:
                    stat_aux[win_player]["里2数"] += 1
                if win["Ura"] >= 3:
                    stat_aux[win_player]["里3+数"] += 1
                if "一发" in win["役种"]:
                    stat_aux[win_player]["一发数"] += 1
    
    stat_df.loc["总局数"] = stat_aux.loc["局数"]
    stat_df.loc["胡牌率"] = stat_aux.loc["胡牌数"] / (stat_aux.loc["局数"] + 1e-15)
    stat_df.loc["自摸率"] = stat_aux.loc["自摸数"] / (stat_aux.loc["胡牌数"] + 1e-15)
    stat_df.loc["放铳率"] = stat_aux.loc["放铳数"] / (stat_aux.loc["局数"] + 1e-15)
    stat_df.loc["立直率"] = stat_aux.loc["立直数"] / (stat_aux.loc["局数"] + 1e-15)
    stat_df.loc["立直胡率"] = stat_aux.loc["立直胡牌数"] / (stat_aux.loc["立直数"] + 1e-15)
    stat_df.loc["立直铳率"] = stat_aux.loc["立直放铳数"] / (stat_aux.loc["立直数"] + 1e-15)
    stat_df.loc["平均打点"] = stat_aux.loc["总打点"] / (stat_aux.loc["胡牌数"] + 1e-15)
    stat_df.loc["立直打点"] = stat_aux.loc["立直打点"] / (stat_aux.loc["立直胡牌数"] + 1e-15)
    stat_df.loc["平均铳点"] = stat_aux.loc["总铳点"] / (stat_aux.loc["放铳数"] + 1e-15)
    stat_df.loc["打点效率"] = stat_df.loc["胡牌率"] * stat_df.loc["平均打点"]
    stat_df.loc["铳点损失"] = stat_df.loc["放铳率"] * stat_df.loc["平均铳点"]
    stat_df.loc["净打点"] = stat_df.loc["打点效率"] - stat_df.loc["铳点损失"]
    stat_df.loc["被炸率"] = stat_aux.loc["被炸数"] / (stat_aux.loc["坐庄数"] + 1e-15)
    stat_df.loc["被炸点"] = stat_aux.loc["被炸点"] / (stat_aux.loc["被炸数"] + 1e-15)
    stat_df.loc["局收支"] = stat_df.loc["素点"] * 1000 / stat_df.loc["总局数"]
    stat_df.loc["悬赏牌"] = (stat_aux.loc["表宝牌数"] + stat_aux.loc["赤宝牌数"] + stat_aux.loc["里宝牌数"]) / (stat_aux.loc["胡牌数"] + 1e-15)
    stat_df.loc["中里率"] = stat_aux.loc["中里次数"] / (stat_aux.loc["立直胡牌数"] + 1e-15)
    stat_df.loc["里2数"] = stat_aux.loc["里2数"]
    stat_df.loc["里3+数"] = stat_aux.loc["里3+数"]
    stat_df.loc["一发率"] = stat_aux.loc["一发数"] / (stat_aux.loc["立直胡牌数"] + 1e-15)

    # 保留小数
    data_index = [
        "总场数", "总局数", "最高点数", "平均打点", "立直打点", "平均铳点", "打点效率", "铳点损失", "净打点",
        "被炸点", "局收支", "里2数", "里3+数"
    ]
    stat_df.loc[data_index] = stat_df.loc[data_index].round(0)
    data_index = ["总得点", "素点"]
    stat_df.loc[data_index] = stat_df.loc[data_index].round(1)
    data_index = ["平均顺位"]
    stat_df.loc[data_index] = stat_df.loc[data_index].round(2)
    data_index = [
        "一位率", "二位率", "三位率", "四位率", "被飞率", "胡牌率", "自摸率", "放铳率",
        "立直率", "立直胡率", "立直铳率", "被炸率", "悬赏牌", "中里率", "一发率"
    ]
    stat_df.loc[data_index] = stat_df.loc[data_index].round(4)

    # 按照总得点排序
    stat_df = stat_df.sort_values(axis=1, by="总得点", ascending=False)
    return stat_df

# 跳满及以上大牌统计
def big_wins(games, players):
    columns = ["半庄名称", "场次", "胡牌者", "是否庄家", "是否自摸", "役种", "宝牌", "赤宝牌", "里宝牌", "番数", "打点"]
    big_wins_df = pd.DataFrame(columns=columns)

    for game in games:
        for one_round in game["对局结果"]:
            dealer = list(game["玩家"].values())[int(one_round["场次"][1]) - 1]
            for win in one_round["胡牌"]:
                ifdealer = "是" if win["胡牌者"] == dealer else "否"
                if ((ifdealer == "是") and (win["打点"] >= 18000)) or ((ifdealer == "否") and (win["打点"] >= 12000)):
                    big_wins_df.loc[len(big_wins_df) + 1] = [
                        game["名称"], one_round["场次"], win["胡牌者"], ifdealer, win["是否自摸"],
                        ", ".join(win["役种"]), win["Dora"], win["Aka"], win["Ura"], win["番数"], win["打点"]
                    ]
    return big_wins_df

# 役种出现频率
def honors_ratio(games):
    honors = load("honors.json")
    honors_list = list(honors.values())
    ratio_df = pd.DataFrame(0.0, index=["总局数", "胡牌数"] + honors_list, columns=["次数", "局数占比", "胡牌占比"])
    for game in games:
        for one_round in game["对局结果"]:
            ratio_df["次数"]["总局数"] += 1
            ratio_df["次数"]["胡牌数"] += len(one_round["胡牌"])
            for win in one_round["胡牌"]:
                honors_appear = list(set(win["役种"]) & set(honors_list))
                for honor in honors_appear:
                    ratio_df["次数"][honor] += 1
    ratio_df["局数占比"] = ratio_df["次数"] / ratio_df["次数"]["总局数"]
    ratio_df["胡牌占比"] = ratio_df["次数"] / ratio_df["次数"]["胡牌数"]
    ratio_df[["局数占比", "胡牌占比"]] *= 100
    ratio_df["局数占比"] = ratio_df["局数占比"].round(2)
    ratio_df["胡牌占比"] = ratio_df["胡牌占比"].round(2)
    ratio_df.loc["总局数", "局数占比"] = ""
    ratio_df.loc["总局数", "胡牌占比"] = ""
    ratio_df.loc["胡牌数", "胡牌占比"] = ""

    return ratio_df

# 个人顺位趋势
def location_trend(games, players, reg_players):
    played_games = {}
    locations = {}
    for player in players:
        played_games[player] = []
        locations[player] = []
    for game in games:
        final_points = sorted(game["最终点数"].items(), key=lambda x: x[1], reverse=True)
        for i in range(4):
            player, _ = final_points[i]
            played_games[player].append(game["名称"])
            locations[player].append(4 - i)

    figs = []
    for player in reg_players:
        fig = px.line(
            x = played_games[player],
            y = locations[player],
            width = min(len(played_games[player]) * 100 + 200, 1680),
            height = 250
        )
        fig.update_traces(mode="markers+lines")
        fig.update_layout(
            title = f"玩家 {player} 的顺位走势",
            xaxis_title = "场次",
            yaxis_title = "顺位",
            yaxis = dict(
                range = [0, 5],
                tickmode = "array",
                tickvals = [4, 3, 2, 1],
                ticktext = ["1", "2", "3", "4"]
            )
        )
        figs.append(fig)
    return figs

# 各局点数趋势图
def point_trend(games):
    figs = []
    for game in games:
        players = list(game["玩家"].values())
        point_df = pd.DataFrame(
            index = [one_round["场次"] for one_round in game["对局结果"]] + ["完场"],
            columns = players
        )
        for player in players:
            for one_round in game["对局结果"]:
                point_df[player][one_round["场次"]] = one_round["局前点数"][player]
            point_df[player]["完场"] = game["最终点数"][player]

        fig = px.line(
            point_df,
            x = point_df.index,
            y = players,
            height = 500
        )
        fig.update_traces(mode="markers+lines")
        fig.update_layout(
            title = f"对局 {game['名称']} 的点数变化趋势",
            xaxis_title = "场次",
            yaxis_title = "点数",
        )
        figs.append(fig)
    figs.reverse()

    return figs

if __name__ == "__main__":
    if not os.path.exists("stats"):
        os.system("mkdir stats")
    
    games = get_all_games()
    players = get_all_players(games)

    stat_df = detailed_stats(games, players)
    reg_th = 15
    reg_players = stat_df.columns[stat_df.loc["总场数"] >= reg_th]
    occ_players = stat_df.columns[stat_df.loc["总场数"] < reg_th]
    sheets = {
        "常客玩家": stat_df[reg_players],
        "游客玩家": stat_df[occ_players]
    }
    excel_writer("stats/详细数据.xlsx", sheets)

    big_wins_df = big_wins(games, players)
    sheets = {"合集": big_wins_df}
    for player in reg_players:
        big_wins_subdf = big_wins_df[big_wins_df["胡牌者"] == player]
        big_wins_subdf = big_wins_subdf.drop("胡牌者", axis=1)
        big_wins_subdf.index = range(1, len(big_wins_subdf) + 1)
        sheets[player] = big_wins_subdf
    excel_writer("stats/大牌统计.xlsx", sheets)

    ratio_df = honors_ratio(games)
    excel_writer("stats/役种频率一览.xlsx", {"役种频率一览": ratio_df})

    figs = location_trend(games, players, reg_players)
    with open("stats/玩家顺位走势.html", "w") as f:
        for fig in figs:
            f.write(fig.to_html(full_html=False, include_plotlyjs="cdn"))

    figs = point_trend(games)
    with open("stats/各局点数变化趋势.html", "w") as f:
        for fig in figs:
            f.write(fig.to_html(full_html=False, include_plotlyjs="cdn"))