# 暂不支持的功能：流局满贯、诈立/诈胡罚分
from utils import *
import copy
import os

# 创建一场对局
def new_game(nickname_file, out_dir):
    if not os.path.exists(f"{out_dir}/{nickname_file}.json"):
        dump({"玩家": {}, "新玩家编号": 0}, f"{out_dir}/{nickname_file}.json")

    print("是否载入未完成的对局[是(y)/否(default)]：", end = ""); if_load = input()
    if if_load == "y":
        while True:
            try:
                print("输入对局名称：", end = ""); game_name = input()
                game = load(f"./{out_dir}/{game_name}.json")
                game_his = load(f"./{out_dir}/{game_name}_his.json")
                break
            except:
                print("对局不存在！")
        return game, game_his

    # 对局名称
    print("输入对局名称：", end = ""); game_name = input()

    # 对局类型
    print("输入对局类型[半庄(default)/东风(e)]：", end = ""); game_type = input()
    if game_type == "e":
        game_type = "东风"
    else:
        game_type = "半庄"

    # 规则类型
    #   默认支持M规/雀魂
    #   其他规则请依照对局中的提示
    print("输入对局规则[M规(m)/雀魂(q)/其他(default)]：", end = ""); game_rule = input()
    if game_rule == "m":
        game_rule = "M规"
    elif game_rule == "q":
        game_rule = "雀魂"
    else:
        game_rule = "其他"

    # 玩家信息
    #   使用拼音首字母提高输入效率
    #   临时玩家用编号"玩家001-玩家999"表示
    game_players = {}
    print("输入玩家昵称：")
    while True:
        nickname_list = load(f"{out_dir}/{nickname_file}.json")
        for loc in ("东家", "南家", "西家", "北家"):
            print(f"{loc}：", end = ""); player_nickname = input()
            if player_nickname in nickname_list["玩家"].keys():
                game_players[loc] = nickname_list["玩家"][player_nickname]
            else:
                print(f"输入新玩家全名（留空则用编号记录）：", end = ""); player_fullname = input()
                if player_fullname == "":
                    game_players[loc] = f"玩家{'{:0>3d}'.format(nickname_list['新玩家编号'])}"
                    nickname_list["新玩家编号"] += 1
                else:
                    game_players[loc] = player_fullname
                    nickname_list["玩家"][player_nickname] = player_fullname
        print(game_players)
        print("玩家全名是否正确？[是(default)/否(n)]：", end = ""); fullname_check = input()
        if fullname_check != "n":
            break
    dump(nickname_list, f"{out_dir}/{nickname_file}.json")

    # 玩家初始点数
    game_points = {
        game_players["东家"]: 25000,
        game_players["南家"]: 25000,
        game_players["西家"]: 25000,
        game_players["北家"]: 25000,
    }

    # 存储对局信息
    game = {
        "名称": game_name,
        "游戏类型": game_type,
        "规则": game_rule,
        "玩家": game_players,
        "对局结果": [],
        "最终点数": {},
    }
    game_his = [{
        "场次": "东",
        "局数": 1,
        "本场数": 0,
        "立直棒": 0,
        "点数": game_points
    }]
    dump(game, f"./{out_dir}/{game_name}.json")
    dump(game_his, f"./{out_dir}/{game_name}_his.json")
    print("\n对局开始!")
    return game, game_his

# 显示当局信息，并询问是否回退一局
def back_round(game, game_his, out_dir):
    while True:
        game_now = copy.deepcopy(game_his[-1])
        round_name = get_round_name(game_now)
        print(f"\n========================={round_name}=========================\n")
        print(f"当前点数：{game_now['点数']}，立直棒：{game_now['立直棒']}根\n")
        print("开始记录本局，或回退至上一局[开始记录(default)/回退(b)]：", end = ""); if_back = input()
        if if_back != "b":
            break
        if len(game_his) == 1:
            print("\n已经到头了，无法回退！")
        else:
            game_name = game["名称"]
            game["对局结果"] = game["对局结果"][:-1]
            game_his = copy.deepcopy(game_his[:-1])
            dump(game, f"./{out_dir}/{game_name}.json")
            dump(game_his, f"./{out_dir}/{game_name}_his.json")
    return game, game_his

# 记录胡牌信息
#   reach_bet为立直棒数
#   add_round为本场数
#   便于处理一炮多响
def new_win(game, game_now, win, reach_bet, add_round):
    # 记录役种
    honors = load("honors.json")
    honors_str = ""
    for (key, value) in honors.items():
        honors_str += f"{value}({key}), "
    honors_str = honors_str[:-2]
    while True:
        try:
            win["役种"] = []
            print(f"役种（用空格分隔）[{honors_str}]："); honors_short = input()
            honors_short = honors_short.split(" ")
            for honor in honors_short:
                win["役种"].append(honors[honor])
            break
        except:
            print("输入有误，请重新输入！")
    
    # 记录宝牌、番、符信息
    print("Dora：", end = ""); win["Dora"] = int(input())
    print("Aka：", end = ""); win["Aka"] = int(input())
    print("Ura：", end = ""); win["Ura"] = int(input())
    print("番数[x番(x)/x倍役满(xbym)]：", end = ""); win["番数"] = input()
    print("符数：", end = ""); fu = int(input()); win["符数"] = fu
    yiman = 0
    if (win["番数"][-3:] == "bym"):
        fan = 0
        yiman = int(win['番数'][:-3])
        win["番数"] = f"{yiman}倍役满"
    else:
        fan = int(win["番数"])
        win["番数"] = fan
    
    # 计算点数
    dealer = get_player_name(game_now, "1")
    rule = game["规则"]
    game_now["点数"][win["胡牌者"]] += reach_bet * 1000
    if win["是否自摸"] == "是":
        point_p, point_d, _, _ = calculate_point(True, yiman, fan, fu, rule)
        if win["胡牌者"] == dealer:
            win["打点"] = point_d * 3
            for player in list(game["玩家"].values()):
                if player == win["胡牌者"]:
                    game_now["点数"][player] += win["打点"] + add_round * 300
                else:
                    game_now["点数"][player] -= point_d + add_round * 100
        else:
            win["打点"] = point_p * 2 + point_d
            for player in list(game["玩家"].values()):
                if player == win["胡牌者"]:
                    game_now["点数"][player] += win["打点"] + add_round * 300
                else:
                    if player == dealer:
                        game_now["点数"][player] -= point_d + add_round * 100
                    else:
                        game_now["点数"][player] -= point_p + add_round * 100
    else:
        _, _, point_fp, point_fd = calculate_point(False, yiman, fan, fu, rule)
        if win["胡牌者"] == dealer:
            win["打点"] = point_fd
        else:
            win["打点"] = point_fp
        game_now["点数"][win["胡牌者"]] += win["打点"] + add_round * 300
        game_now["点数"][win["放铳者"]] -= win["打点"] + add_round * 300
    print(f"打点：{win['打点']}")

# 创建新的一局
def new_round(game, game_his, out_dir):
    game_now = copy.deepcopy(game_his[-1])
    round_name = get_round_name(game_now)
    round_info = {
        "场次": round_name,
        "立直家": [],
        "胡牌": [],
        "局前点数": copy.deepcopy(game_now["点数"]),
        "局后点数": {},
    }
    print()

    while True:
        try:
            print("立直家（用空格分隔）[东家(1)，南家(2)，西家(3), 北家(4)]：", end = "")
            reach_players_id = input()
            reach_players = get_players_name(game_now, reach_players_id)
            break
        except:
            print("输入有误，请重新输入！")
    round_info["立直家"] = reach_players
    for player in reach_players:
        game_now["点数"][player] -= 1000
        game_now["立直棒"] += 1

    print("是否流局[是(y)/否(default)]：", end = ""); draw = input()
    if draw == "y":
        print("流局类型[荒牌流局(default)/其他途中流局(o)]：", end = ""); draw_type = input()
        if draw_type != "o":
            # 计算听牌料
            while True:
                try:
                    print("听牌者（用空格分隔）[东家(1)，南家(2)，西家(3), 北家(4)]：", end = "")
                    ready_players_id = input()
                    ready_players = get_players_name(game_now, ready_players_id)
                    break
                except:
                    print("输入有误，请重新输入！")
            if (len(ready_players) >= 1) and (len(ready_players) <= 3):
                for i in range(len(game["玩家"])):
                    player = list(game["玩家"].values())[i]
                    if player in ready_players:
                        game_now["点数"][player] += int(3000 / len(ready_players))
                    else:
                        game_now["点数"][player] -= int(3000 / (4 - len(ready_players)))
            cont_dealer = get_player_name(game_now, "1") in ready_players
        else: 
            if game["规则"] == "M规":
                print("M规没有途中流局，请检查！")
                return None, None
            cont_dealer = True
        round_info["局后点数"] = copy.deepcopy(game_now["点数"])
        game["对局结果"].append(round_info)
        game_his.append(game_now)
        return cont_dealer, True

    # elif draw == "n": 未流局
    while True:
        try:
            print("胡牌者（一炮多响用空格分隔）[东家(1)，南家(2)，西家(3), 北家(4)]：", end = "")
            win_players_id = input()
            win_players = get_players_name(game_now, win_players_id)
            break
        except:
            print("输入有误，请重新输入！")
    if len(win_players) == 0:
        print("未流局时必有玩家胡牌，请检查！")
        return None, None
    if (game["规则"] == "M规") and (len(win_players) > 1):
        print("M规不支持一炮多响，请检查！")
        return None, None

    while True:
        try:
            print("放铳者（留空表示自摸）[东家(1)/南家(2)/西家(3)/北家(4)]：", end = "")
            fire_player_id = input()
            if fire_player_id != "":
                fire_player = get_player_name(game_now, fire_player_id)
            break
        except:
            print("输入有误，请重新输入！")
    if len(fire_player_id) > 1:
        print("放铳玩家最多只有一名，请检查！")
        return None, None
    if (fire_player_id != "") and (fire_player_id in win_players_id):
        print("胡牌玩家不可能放铳，请检查！")
        return None, None
    if (len(win_players) > 1) and (fire_player_id == ""):
        print("一炮多响必有玩家放铳，请检查！")
        return None, None

    if len(win_players) == 1:
        win = {
            "胡牌者": win_players[0],
            "是否自摸": "",
            "放铳者": "",
        }
        if fire_player_id == "":
            win["是否自摸"] = "是"
        else:
            win["是否自摸"] = "否"
            win["放铳者"] = fire_player
        new_win(game, game_now, win, game_now["立直棒"], game_now["本场数"])
        round_info["胡牌"].append(win)
        game_now["立直棒"] = 0

    # 处理一炮多响
    if len(win_players) > 1:
        win_id = 1
        fire_player_id = int(fire_player_id)
        reach_bet = game_now["立直棒"]
        add_round = game_now["本场数"]
        game_now["立直棒"] = 0
        for i in range(fire_player_id + 1, fire_player_id + 4):
            player_id = str(((i - 1) % 4) + 1)
            if player_id in win_players_id.split(" "):
                str_win_id = {"1": "东家", "2": "南家", "3": "西家", "4": "北家"}
                print(f"\n第{win_id}位胡牌者[{str_win_id[player_id]}]：")

                win = {
                    "胡牌者": get_player_name(game_now, player_id),
                    "是否自摸": "否",
                    "放铳者": fire_player,
                }

                # 注意本场数供托、立直棒头跳
                new_win(game, game_now, win, reach_bet, add_round)
                reach_bet = 0; add_round = 0
                win_id += 1
                round_info["胡牌"].append(win)

    round_info["局后点数"] = copy.deepcopy(game_now["点数"])
    game["对局结果"].append(round_info)
    game_his.append(game_now)
    return "1" in win_players_id.split(" "), False

# 根据是否连庄、是否流局得出下一局次信息
def post_round(game, game_his, cont_dealer, draw, out_dir):
    # 存储对局结果
    game_now = game_his[-1]
    if draw or cont_dealer:
        game_now["本场数"] += 1
    else:
        game_now["本场数"] = 0

    # 判断有玩家被击飞后游戏是否结束
    if min(list(game_now["点数"].values())) < 0:
        if game["规则"] == "雀魂":
            return True
        elif game["规则"] == "其他":
            print("\n已有玩家被击飞，游戏是否继续？[是(default)/否(n)]：", end = ""); cont_game = input()
            if cont_game == "n":
                return True

    # 处理下一局次信息
    reach_30k = max(game_now["点数"].values()) >= 30000
    if (game["游戏类型"] == "半庄") and (game_now["场次"] == "西") and reach_30k:
        return True
    if (game["游戏类型"] == "东风") and (game_now["场次"] == "南") and reach_30k:
        return True

    if cont_dealer:
        return False
    game_now["局数"] = game_now["局数"] % 4 + 1
    if game_now["局数"] > 1:
        return False
    if (game["游戏类型"] == "半庄") and (game_now["场次"] == "东"):
        game_now["场次"] = "南"
        return False
    if (game["游戏类型"] == "半庄") and (game_now["场次"] == "西"):
        return True
    if (game["游戏类型"] == "东风") and (game_now["场次"] == "南"):
        return True

    # M规永不西入/南入
    if game["规则"] == "M规":
        return True

    # 雀魂规在最高点数不足30000点时需西入/南入
    elif game["规则"] == "雀魂":
        if not reach_30k:
            if game["游戏类型"] == "半庄":
                game_now["场次"] = "西"
            elif game["游戏类型"] == "东风":
                game_now["场次"] = "南"
            return False
        return True

    # 其他规则下询问是否西入/南入
    elif game["规则"] == "其他":
        if not reach_30k:
            print("\n还未有玩家达到30000分，是否西(南)入？[是(y)/否(default)]：", end = ""); cont_game = input()
            if cont_game != "y":
                return True
            if game["游戏类型"] == "半庄":
                game_now["场次"] = "西"
            elif game["游戏类型"] == "东风":
                game_now["场次"] = "南"
            return False
        return True
    
    return False

# 对局结束后一位获得场上未确认归属的立直棒
def end_game(game, game_his, out_dir):
    game_now = game_his[-1]
    points = list(game_now["点数"].values())
    max_id = 0
    for i in range(4):
        if points[max_id] < points[i]:
            max_id = i
    game_now["点数"][list(game["玩家"].values())[max_id]] += game_now["立直棒"] * 1000
    
    game["最终点数"] = game_now["点数"].copy()
    print(f"\n对局结束!\n\n最终点数：{game_now['点数']}\n")
    dump(game, f"./{out_dir}/{game['名称']}.json")
    os.remove(f"./{out_dir}/{game['名称']}_his.json")

if __name__ == "__main__":
    out_dir = "data"
    nickname_file = "nickname_list"
    game, game_his = new_game(nickname_file, out_dir)
    while True:
        game, game_his = back_round(game, game_his, out_dir)
        cont_dealer, draw = new_round(game, game_his, out_dir)
        if draw != None: # draw = None表示对局中出现问题
            stop_game = post_round(game, game_his, cont_dealer, draw, out_dir)
            dump(game, f"./{out_dir}/{game['名称']}.json")
            dump(game_his, f"./{out_dir}/{game['名称']}_his.json")
            if stop_game:
                break
    end_game(game, game_his, out_dir)