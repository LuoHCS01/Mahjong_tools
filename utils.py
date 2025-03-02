import math
import json
import pandas as pd

# 读取json文件
def load(filename):
    return json.load(open(filename, "r", encoding="utf-8"))

# 存储至json文件
def dump(data, filename):
    fw = open(filename, "w", encoding="utf-8")
    json.dump(data, fw, indent=4, ensure_ascii=False)
    fw.close()

# 获取局次，如"东1局0本场"
def get_round_name(game_now):
    return f"{game_now['场次']}{game_now['局数']}局{game_now['本场数']}本场"

# 根据当前所在位置（东南西北）获取玩家名称
def get_players_name(game_now, players_str):
    players_fullname = list(game_now["点数"].keys())
    if players_str == "":
        fullname_list = []
    else:
        fullname_list = players_str.split(" ")
        for i in range(len(fullname_list)):
            index = (int(fullname_list[i]) + game_now["局数"] - 2) % 4
            fullname_list[i] = players_fullname[index]
    return fullname_list

def get_player_name(game_now, player_str):
    return get_players_name(game_now, player_str)[0]

# 计算打点
def calculate_point(owndraw, yiman, fan, fu, rule):
    if yiman > 0:
        a = 8000 * yiman
        return a, 2 * a, 4 * a, 6 * a
    if fan >= 5:
        if fan >= 13:
            if rule == "雀魂":
                a = 8000
            elif rule == "M规":
                a = 6000
            else:
                print("是否计累计役满[是(y)/否(default)]:", end = ""); if_yiman = input()
                if if_yiman == "y":
                    a = 8000
                else:
                    a = 6000
        elif (fan >= 11) and (fan <= 12):
            a = 6000
        elif (fan >= 8) and (fan <= 10):
            a = 4000
        elif (fan >= 6) and (fan <= 7):
            a = 3000
        else:
            a = 2000
        return a, 2 * a, 4 * a, 6 * a
    # elif fan <= 4
    if owndraw:
        point_p = min(math.ceil(0.04 * fu * 2 ** fan) * 100, 2000)
        point_d = min(math.ceil(0.08 * fu * 2 ** fan) * 100, 4000)
        if point_d == 3900:
            if rule == "M规":
                point_d = 4000
            elif rule == "其他":
                print("是否计切上满贯[是(default)/否(n)]:", end = ""); if_manguan = input()
                if if_manguan != "n":
                    point_d = 4000
        return point_p, point_d, 0, 0
    else:
        point_fp = min(math.ceil(0.16 * fu * 2 ** fan) * 100, 8000)
        point_fd = min(math.ceil(0.24 * fu * 2 ** fan) * 100, 12000)
        if (point_fp == 7700) or (point_fd == 11600):
            if rule == "M规":
                point_fp = 8000
                point_fd = 12000
            elif rule == "其他":
                print("是否计切上满贯[是(default)/否(n)]:", end = ""); if_manguan = input()
                if if_manguan != "n":
                    point_fp = 8000
                    point_fd = 12000
        return 0, 0, point_fp, point_fd

# excel_writer: 调整列宽时获得字符串长度
def get_length(element):
    length = 0
    for c in list(str(element)):
        if ord(c) <= 256:
            length += 1
        else:
            length += 2
    return length

def number_to_excel_column(n):
    column_name = ""
    n += 1
    while n > 0:
        n -= 1
        column_name = chr(n % 26 + ord('A')) + column_name
        n //= 26
    return column_name

def excel_writer(filename, sheets: dict):
    writer = pd.ExcelWriter(filename)
    for sheet_name, df in sheets.items():
        df.to_excel(writer, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]
        for index, column in enumerate(df):
            max_len = get_length(df[column].name)
            for entry in list(df[column]):
                max_len = max(max_len, get_length(entry))
            worksheet.column_dimensions[number_to_excel_column(index + 1)].width = max_len + 2
        max_len = 0
        for entry in list(df.index):
            max_len = max(max_len, get_length(entry))
        worksheet.column_dimensions[number_to_excel_column(0)].width = max_len + 2
    writer._save()