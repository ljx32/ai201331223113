import pygame
import random
import math
import os
import json
import datetime

# 初始化
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# 玩家颜色选项
PLAYER_COLORS = [
    (50, 255, 100),  # 绿色
    (100, 150, 255),  # 蓝色
    (255, 100, 150),  # 粉色
    (255, 200, 50),  # 黄色
    (150, 50, 255),  # 紫色
    (50, 255, 255),  # 青色
]

PLAYER_COLOR_NAMES = [
    "绿色",
    "蓝色",
    "粉色",
    "黄色",
    "紫色",
    "青色"
]


# 字体处理函数
def get_font_path():
    if os.path.exists("simhei.ttf"):
        return "simhei.ttf"

    if os.name == 'nt':
        possible_fonts = [
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/simkai.ttf",
        ]
    else:
        possible_fonts = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]

    for font_path in possible_fonts:
        if os.path.exists(font_path):
            return font_path

    return None


class FontManager:
    def __init__(self):
        self.font_path = get_font_path()
        self.fonts = {}

    def get_font(self, size):
        if size not in self.fonts:
            if self.font_path:
                try:
                    self.fonts[size] = pygame.font.Font(self.font_path, size)
                except:
                    self.fonts[size] = pygame.font.SysFont(None, size)
            else:
                chinese_fonts = ['simhei', 'microsoftyahei', 'fangsong', 'simsun']
                for font_name in chinese_fonts:
                    try:
                        self.fonts[size] = pygame.font.SysFont(font_name, size)
                        break
                    except:
                        continue
                else:
                    self.fonts[size] = pygame.font.SysFont(None, size)
        return self.fonts[size]


# 创建字体管理器
font_manager = FontManager()


class GameRanking:
    def __init__(self, filename="game_scores.json"):
        self.filename = filename
        self.scores = self.load_scores()

    def load_scores(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载分数失败: {e}")

        return {
            "highest_score": 0,
            "records": []
        }

    def save_scores(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.scores, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存分数失败: {e}")

    def add_score(self, score, lives_remaining=0):
        new_record = {
            "score": score,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "lives": lives_remaining
        }

        self.scores["records"].append(new_record)
        self.scores["records"].sort(key=lambda x: x["score"], reverse=True)
        self.scores["records"] = self.scores["records"][:10]

        if score > self.scores["highest_score"]:
            self.scores["highest_score"] = score

        self.save_scores()

    def get_top_scores(self, count=5):
        return self.scores["records"][:count]

    def get_highest_score(self):
        return self.scores["highest_score"]

    def get_total_games(self):
        return len(self.scores["records"])


class AIDodger:
    def __init__(self):
        # 玩家
        self.player_pos = [WIDTH // 2, HEIGHT // 2]
        self.player_size = 25

        # 玩家颜色
        self.player_color_index = 0
        self.player_color = PLAYER_COLORS[0]
        self.show_color_menu = False

        # 障碍物
        self.obstacles = []
        self.spawn_timer = 0
        self.spawn_rate = 30

        # 道具
        self.powerups = []
        self.powerup_timer = 0

        # 游戏状态
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.slow_time = 0

        # AI追踪器
        self.ai_trackers = []

        # 暂停状态
        self.paused = False
        self.pause_blink = 0
        self.pause_text_visible = True

        # 排名系统
        self.ranking = GameRanking()
        self.show_ranking = False
        self.ranking_scroll = 0
        self.ranking_animation = 0

        # 颜色选择动画
        self.color_menu_animation = 0
        self.color_selection_pulse = 0

    def toggle_pause(self):
        self.paused = not self.paused

    def draw_color_menu(self, screen, x, y, width, height):
        """绘制颜色选择菜单"""
        font_normal = font_manager.get_font(28)
        font_title = font_manager.get_font(36)
        font_small = font_manager.get_font(22)

        # 绘制菜单背景
        menu_bg = pygame.Surface((width, height), pygame.SRCALPHA)
        menu_bg.fill((0, 0, 0, 200))
        pygame.draw.rect(menu_bg, (80, 80, 120), menu_bg.get_rect(), 3)

        # 绘制标题
        title = font_title.render("🎨 选择玩家颜色 🎨", True, (255, 255, 200))
        menu_bg.blit(title, (width // 2 - title.get_width() // 2, 15))

        # 绘制当前颜色预览
        preview_size = 80
        pygame.draw.circle(menu_bg, self.player_color,
                           (width // 2, 100), preview_size)

        # 绘制当前颜色边框（脉冲效果）
        pulse_width = 3 + int(math.sin(self.color_selection_pulse * 0.1) * 2)
        pygame.draw.circle(menu_bg, (255, 255, 255),
                           (width // 2, 100), preview_size + pulse_width, pulse_width)

        # 绘制颜色名称
        color_name = font_normal.render(PLAYER_COLOR_NAMES[self.player_color_index], True, (255, 255, 255))
        menu_bg.blit(color_name, (width // 2 - color_name.get_width() // 2, 180))

        # 绘制颜色选项网格
        color_grid_y = 220
        color_size = 50
        color_spacing = 20

        cols = 3
        total_width = cols * color_size + (cols - 1) * color_spacing
        start_x = (width - total_width) // 2

        for i, color in enumerate(PLAYER_COLORS):
            row = i // cols
            col = i % cols

            color_x = start_x + col * (color_size + color_spacing)
            color_y = color_grid_y + row * (color_size + color_spacing)

            # 绘制颜色方块
            pygame.draw.rect(menu_bg, color,
                             (color_x, color_y, color_size, color_size))

            # 绘制边框
            border_color = (255, 255, 255) if i == self.player_color_index else (100, 100, 100)
            border_width = 3 if i == self.player_color_index else 1
            pygame.draw.rect(menu_bg, border_color,
                             (color_x, color_y, color_size, color_size), border_width)

            # 如果是当前选中的颜色，添加选中标记
            if i == self.player_color_index:
                check_points = [
                    (color_x + 10, color_y + color_size // 2),
                    (color_x + color_size // 2 - 5, color_y + color_size - 10),
                    (color_x + color_size - 10, color_y + 10)
                ]
                pygame.draw.lines(menu_bg, (255, 255, 255), False, check_points, 3)

        # 绘制操作提示
        instructions_y = color_grid_y + 2 * (color_size + color_spacing) + 20

        hint1 = font_normal.render("使用 ← → 键选择颜色", True, (200, 200, 255))
        hint2 = font_normal.render("按 Enter 键确认选择", True, (200, 200, 255))
        hint3 = font_normal.render("按 C 键或 ESC 键取消", True, (200, 200, 255))

        menu_bg.blit(hint1, (width // 2 - hint1.get_width() // 2, instructions_y))
        menu_bg.blit(hint2, (width // 2 - hint2.get_width() // 2, instructions_y + 35))
        menu_bg.blit(hint3, (width // 2 - hint3.get_width() // 2, instructions_y + 70))

        # 绘制动画效果
        self.color_menu_animation = (self.color_menu_animation + 1) % 60
        if self.color_menu_animation < 30:
            pygame.draw.rect(menu_bg, (255, 200, 50, 100), menu_bg.get_rect(), 2)

        screen.blit(menu_bg, (x, y))

    def spawn_obstacle(self):
        side = random.choice(['top', 'right', 'bottom', 'left'])
        if side == 'top':
            x, y = random.randint(0, WIDTH), -20
            speed = random.uniform(2, 4)
        elif side == 'right':
            x, y = WIDTH + 20, random.randint(0, HEIGHT)
            speed = random.uniform(2, 4)
        elif side == 'bottom':
            x, y = random.randint(0, WIDTH), HEIGHT + 20
            speed = random.uniform(2, 4)
        else:
            x, y = -20, random.randint(0, HEIGHT)
            speed = random.uniform(2, 4)

        self.obstacles.append({
            'pos': [x, y],
            'size': random.randint(15, 30),
            'speed': speed,
            'color': (random.randint(200, 255), random.randint(50, 100), random.randint(50, 100)),
            'type': 'normal'
        })

    def spawn_ai_tracker(self):
        side = random.choice(['top', 'right', 'bottom', 'left'])
        if side == 'top':
            x, y = random.randint(0, WIDTH), -20
        elif side == 'right':
            x, y = WIDTH + 20, random.randint(0, HEIGHT)
        elif side == 'bottom':
            x, y = random.randint(0, WIDTH), HEIGHT + 20
        else:
            x, y = -20, random.randint(0, HEIGHT)

        self.ai_trackers.append({
            'pos': [x, y],
            'size': 20,
            'speed': random.uniform(1.5, 2.5),
            'color': (255, 100, 100),
            'track_strength': random.uniform(0.3, 0.7)
        })

    def spawn_powerup(self):
        types = ['score', 'shield', 'bomb', 'slow']
        type_choice = random.choice(types)
        self.powerups.append({
            'pos': [random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50)],
            'size': 15,
            'type': type_choice,
            'color': (0, 200, 255) if type_choice == 'score' else
            (255, 200, 0) if type_choice == 'shield' else
            (255, 100, 255) if type_choice == 'bomb' else
            (100, 255, 255),
            'timer': 300
        })

    def update(self):
        if self.game_over:
            return

        if self.paused:
            self.pause_blink = (self.pause_blink + 1) % 60
            self.pause_text_visible = self.pause_blink < 30
            return

        if self.show_color_menu:
            self.color_selection_pulse += 1
            return

        # 玩家跟随鼠标
        mouse_pos = pygame.mouse.get_pos()
        dx = mouse_pos[0] - self.player_pos[0]
        dy = mouse_pos[1] - self.player_pos[1]
        distance = math.sqrt(dx * dx + dy * dy)
        if distance > 0:
            move_speed = min(8, distance / 5)
            self.player_pos[0] += dx / distance * move_speed
            self.player_pos[1] += dy / distance * move_speed

        # 生成障碍物
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_rate:
            self.spawn_obstacle()
            self.spawn_timer = 0

            if self.score % 500 == 0 and len(self.ai_trackers) < 5:
                self.spawn_ai_tracker()

        # 生成道具
        self.powerup_timer += 1
        if self.powerup_timer >= 450:
            self.spawn_powerup()
            self.powerup_timer = 0

        # 更新障碍物
        for obs in self.obstacles[:]:
            dx = self.player_pos[0] - obs['pos'][0]
            dy = self.player_pos[1] - obs['pos'][1]
            dist = max(math.sqrt(dx * dx + dy * dy), 0.1)

            speed_mod = 1.0
            if dist < 100:
                speed_mod = 0.7

            if self.slow_time > 0:
                speed_mod *= 0.5

            obs['pos'][0] += dx / dist * obs['speed'] * speed_mod
            obs['pos'][1] += dy / dist * obs['speed'] * speed_mod

            if (obs['pos'][0] < -100 or obs['pos'][0] > WIDTH + 100 or
                    obs['pos'][1] < -100 or obs['pos'][1] > HEIGHT + 100):
                self.obstacles.remove(obs)
                self.score += 5

        # 更新AI追踪器
        for tracker in self.ai_trackers[:]:
            dx = self.player_pos[0] - tracker['pos'][0]
            dy = self.player_pos[1] - tracker['pos'][1]
            dist = max(math.sqrt(dx * dx + dy * dy), 0.1)

            tracker['pos'][0] += dx / dist * tracker['speed'] * tracker['track_strength']
            tracker['pos'][1] += dy / dist * tracker['speed'] * tracker['track_strength']

            tracker['pos'][0] += random.uniform(-1, 1)
            tracker['pos'][1] += random.uniform(-1, 1)

        # 更新道具
        for powerup in self.powerups[:]:
            powerup['timer'] -= 1
            if powerup['timer'] <= 0:
                self.powerups.remove(powerup)

        # 检测碰撞
        self.check_collisions()

        # 更新分数
        self.score += 1

        # 更新减速效果
        if self.slow_time > 0:
            self.slow_time -= 1

        # 调整生成速度
        self.spawn_rate = max(15, 30 - self.score // 500)

    def check_collisions(self):
        player_rect = pygame.Rect(self.player_pos[0] - self.player_size,
                                  self.player_pos[1] - self.player_size,
                                  self.player_size * 2, self.player_size * 2)

        for obs in self.obstacles[:]:
            obs_rect = pygame.Rect(obs['pos'][0] - obs['size'],
                                   obs['pos'][1] - obs['size'],
                                   obs['size'] * 2, obs['size'] * 2)
            if player_rect.colliderect(obs_rect):
                self.lives -= 1
                self.obstacles.remove(obs)
                if self.lives <= 0:
                    self.game_over = True
                    self.ranking.add_score(self.score, self.lives)

        for tracker in self.ai_trackers[:]:
            tracker_rect = pygame.Rect(tracker['pos'][0] - tracker['size'],
                                       tracker['pos'][1] - tracker['size'],
                                       tracker['size'] * 2, tracker['size'] * 2)
            if player_rect.colliderect(tracker_rect):
                self.lives -= 2
                self.ai_trackers.remove(tracker)
                if self.lives <= 0:
                    self.game_over = True
                    self.ranking.add_score(self.score, self.lives)

        for powerup in self.powerups[:]:
            powerup_rect = pygame.Rect(powerup['pos'][0] - powerup['size'],
                                       powerup['pos'][1] - powerup['size'],
                                       powerup['size'] * 2, powerup['size'] * 2)
            if player_rect.colliderect(powerup_rect):
                self.apply_powerup(powerup['type'])
                self.powerups.remove(powerup)

    def apply_powerup(self, powerup_type):
        if powerup_type == 'score':
            self.score += 200
        elif powerup_type == 'shield':
            self.lives = min(5, self.lives + 1)
        elif powerup_type == 'bomb':
            self.obstacles.clear()
            self.score += 100
        elif powerup_type == 'slow':
            self.slow_time = 300

    def draw_ranking(self, screen, x, y, width, height):
        font_normal = font_manager.get_font(28)
        font_small = font_manager.get_font(22)
        font_title = font_manager.get_font(36)

        ranking_bg = pygame.Surface((width, height), pygame.SRCALPHA)
        ranking_bg.fill((0, 0, 0, 180))
        pygame.draw.rect(ranking_bg, (50, 50, 100), ranking_bg.get_rect(), 3)

        title = font_title.render("🏆 游戏排名 🏆", True, (255, 215, 0))
        ranking_bg.blit(title, (width // 2 - title.get_width() // 2, 15))

        highest_score = font_normal.render(f"历史最高分: {self.ranking.get_highest_score()}", True, (255, 100, 100))
        ranking_bg.blit(highest_score, (width // 2 - highest_score.get_width() // 2, 60))

        total_games = font_small.render(f"总游戏次数: {self.ranking.get_total_games()}", True, (150, 150, 255))
        ranking_bg.blit(total_games, (width // 2 - total_games.get_width() // 2, 90))

        headers = ["排名", "分数", "剩余生命", "日期"]
        header_y = 130
        col_widths = [60, 100, 80, 150]

        pygame.draw.rect(ranking_bg, (30, 30, 70), (20, header_y - 5, width - 40, 30))

        current_x = 25
        for i, header in enumerate(headers):
            header_text = font_normal.render(header, True, (200, 200, 255))
            ranking_bg.blit(header_text, (current_x, header_y))
            current_x += col_widths[i]

        pygame.draw.line(ranking_bg, (100, 100, 150), (20, header_y + 35), (width - 20, header_y + 35), 2)

        top_scores = self.ranking.get_top_scores(10)

        start_y = header_y + 45
        row_height = 35

        for i in range(min(len(top_scores) - self.ranking_scroll, 5)):
            idx = i + self.ranking_scroll
            if idx >= len(top_scores):
                break

            record = top_scores[idx]

            row_color = (40, 40, 80, 180) if i % 2 == 0 else (50, 50, 90, 180)
            pygame.draw.rect(ranking_bg, row_color, (20, start_y + i * row_height, width - 40, row_height - 5))

            rank_text = font_normal.render(f"{idx + 1}.", True, (255, 215, 0))
            ranking_bg.blit(rank_text, (30, start_y + i * row_height + 5))

            score_color = (255, 100, 100) if record["score"] == self.ranking.get_highest_score() else (255, 255, 255)
            score_text = font_normal.render(str(record["score"]), True, score_color)
            ranking_bg.blit(score_text, (90, start_y + i * row_height + 5))

            lives_text = font_normal.render("♥" * record["lives"], True, (255, 50, 50))
            ranking_bg.blit(lives_text, (200, start_y + i * row_height + 5))

            date_text = font_small.render(record["date"], True, (150, 200, 150))
            ranking_bg.blit(date_text, (290, start_y + i * row_height + 8))

        if len(top_scores) == 0:
            no_data = font_normal.render("暂无游戏记录，开始你的第一局游戏吧！", True, (200, 200, 200))
            ranking_bg.blit(no_data, (width // 2 - no_data.get_width() // 2, start_y + 50))

        if len(top_scores) > 5:
            scroll_hint = font_small.render(
                f"↑↓ 滚动查看更多记录 ({self.ranking_scroll + 1}-{min(self.ranking_scroll + 5, len(top_scores))}/{len(top_scores)})",
                True, (150, 150, 255))
            ranking_bg.blit(scroll_hint, (width // 2 - scroll_hint.get_width() // 2, height - 40))

        hint = font_small.render("按 T 键关闭排名", True, (100, 255, 100))
        ranking_bg.blit(hint, (width // 2 - hint.get_width() // 2, height - 20))

        self.ranking_animation = (self.ranking_animation + 1) % 60
        if self.ranking_animation < 30:
            pygame.draw.rect(ranking_bg, (255, 215, 0, 150), ranking_bg.get_rect(), 2)

        screen.blit(ranking_bg, (x, y))

    def draw(self, screen):
        screen.fill((10, 10, 20))

        for _ in range(50):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.randint(1, 3)
            pygame.draw.circle(screen, (100, 100, 150), (x, y), size)

        # 绘制玩家（使用选择的颜色）
        pygame.draw.circle(screen, self.player_color,
                           (int(self.player_pos[0]), int(self.player_pos[1])),
                           self.player_size)

        # 玩家中心点
        center_color = (
            min(255, self.player_color[0] + 100),
            min(255, self.player_color[1] + 100),
            min(255, self.player_color[2] + 100)
        )
        pygame.draw.circle(screen, center_color,
                           (int(self.player_pos[0]), int(self.player_pos[1])),
                           self.player_size // 3)

        if self.slow_time > 0:
            pygame.draw.circle(screen, (100, 100, 255),
                               (int(self.player_pos[0]), int(self.player_pos[1])),
                               self.player_size + 10, 3)

        for obs in self.obstacles:
            pygame.draw.circle(screen, obs['color'],
                               (int(obs['pos'][0]), int(obs['pos'][1])),
                               obs['size'])
            pygame.draw.circle(screen, (255, 255, 255),
                               (int(obs['pos'][0]), int(obs['pos'][1])),
                               obs['size'], 2)

        for tracker in self.ai_trackers:
            pygame.draw.circle(screen, tracker['color'],
                               (int(tracker['pos'][0]), int(tracker['pos'][1])),
                               tracker['size'])
            pygame.draw.circle(screen, (255, 50, 50),
                               (int(tracker['pos'][0]), int(tracker['pos'][1])),
                               tracker['size'] // 2)
            pygame.draw.circle(screen, (255, 255, 255),
                               (int(tracker['pos'][0]), int(tracker['pos'][1])),
                               tracker['size'] // 3)

        for powerup in self.powerups:
            color = powerup['color']
            pos = powerup['pos']
            size = powerup['size']

            if powerup['type'] == 'score':
                pygame.draw.circle(screen, (255, 215, 0), (int(pos[0]), int(pos[1])), size)
                pygame.draw.circle(screen, (255, 255, 0), (int(pos[0]), int(pos[1])), size - 3)
            elif powerup['type'] == 'shield':
                pygame.draw.circle(screen, (0, 200, 255), (int(pos[0]), int(pos[1])), size)
                pygame.draw.circle(screen, (200, 230, 255), (int(pos[0]), int(pos[1])), size - 5)
            elif powerup['type'] == 'bomb':
                pygame.draw.circle(screen, (255, 100, 100), (int(pos[0]), int(pos[1])), size)
                pygame.draw.circle(screen, (255, 150, 150), (int(pos[0]), int(pos[1])), size - 3)
            else:
                pygame.draw.circle(screen, (100, 100, 255), (int(pos[0]), int(pos[1])), size)

        font_normal = font_manager.get_font(36)
        font_small = font_manager.get_font(24)
        font_large = font_manager.get_font(72)

        # 显示当前颜色
        color_indicator = font_small.render(f"颜色: {PLAYER_COLOR_NAMES[self.player_color_index]}", True,
                                            self.player_color)
        screen.blit(color_indicator, (WIDTH - color_indicator.get_width() - 10, 10))

        score_text = font_normal.render(f"分数: {self.score}", True, (255, 255, 255))
        lives_text = font_normal.render(f"生命: {self.lives}", True, (255, 50, 50))
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (10, 50))

        ai_text = font_normal.render(f"AI追踪者: {len(self.ai_trackers)}", True, (255, 100, 100))
        screen.blit(ai_text, (10, 90))

        controls = font_normal.render("移动鼠标躲避障碍物 | ESC退出 | R重新开始", True, (150, 200, 255))
        screen.blit(controls, (WIDTH // 2 - controls.get_width() // 2, HEIGHT - 40))

        if not self.show_color_menu and not self.show_ranking and not self.game_over and not self.paused:
            pause_hint = font_normal.render("按 P 或空格键暂停游戏", True, (100, 200, 100))
            screen.blit(pause_hint, (WIDTH // 2 - pause_hint.get_width() // 2, HEIGHT - 80))

            rank_hint = font_small.render("按 T 键查看排名", True, (200, 200, 100))
            screen.blit(rank_hint, (WIDTH - rank_hint.get_width() - 10, 130))

            color_hint = font_small.render("按 C 键更改玩家颜色", True, (200, 200, 100))
            screen.blit(color_hint, (WIDTH - color_hint.get_width() - 10, 160))

        if self.show_color_menu:
            menu_width = 500
            menu_height = 450
            menu_x = WIDTH // 2 - menu_width // 2
            menu_y = HEIGHT // 2 - menu_height // 2

            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            self.draw_color_menu(screen, menu_x, menu_y, menu_width, menu_height)

            if not self.paused and not self.game_over:
                status_text = font_normal.render(f"当前游戏暂停中... 分数: {self.score} 生命: {self.lives}", True,
                                                 (255, 255, 100))
                screen.blit(status_text, (WIDTH // 2 - status_text.get_width() // 2, menu_y - 50))

        if self.show_ranking:
            ranking_width = 600
            ranking_height = 500
            ranking_x = WIDTH // 2 - ranking_width // 2
            ranking_y = HEIGHT // 2 - ranking_height // 2

            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            self.draw_ranking(screen, ranking_x, ranking_y, ranking_width, ranking_height)

            if not self.paused and not self.game_over:
                status_text = font_normal.render(f"当前游戏暂停中... 分数: {self.score} 生命: {self.lives}", True,
                                                 (255, 255, 100))
                screen.blit(status_text, (WIDTH // 2 - status_text.get_width() // 2, ranking_y - 50))

        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            game_over_text = font_large.render("游戏结束!", True, (255, 50, 50))
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))

            final_score = font_normal.render(f"最终分数: {self.score}", True, (255, 255, 255))
            screen.blit(final_score, (WIDTH // 2 - final_score.get_width() // 2, HEIGHT // 2 + 20))

            restart_text = font_normal.render("按 R 重新开始", True, (50, 255, 100))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 80))

            ranking_button = font_normal.render("按 T 键查看排名", True, (100, 255, 255))
            screen.blit(ranking_button, (WIDTH // 2 - ranking_button.get_width() // 2, HEIGHT // 2 + 120))

            color_button = font_normal.render("按 C 键更改颜色后重新开始", True, (255, 200, 100))
            screen.blit(color_button, (WIDTH // 2 - color_button.get_width() // 2, HEIGHT // 2 + 160))

            top_scores = self.ranking.get_top_scores(5)
            for i, record in enumerate(top_scores):
                if self.score == record["score"]:
                    rank_position = font_small.render(f"🎯 本次得分排名第 {i + 1} 名！", True, (255, 215, 0))
                    screen.blit(rank_position, (WIDTH // 2 - rank_position.get_width() // 2, HEIGHT // 2 + 200))
                    break

        if self.paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))

            if self.pause_text_visible:
                pause_text = font_large.render("游戏暂停", True, (255, 255, 100))
                screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - 50))

            instructions = font_normal.render("按 P 或空格键继续游戏", True, (200, 200, 255))
            screen.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, HEIGHT // 2 + 50))

            hint1 = font_normal.render("按 ESC 退出游戏", True, (150, 150, 200))
            hint2 = font_normal.render("按 R 重新开始（如果游戏结束）", True, (150, 150, 200))
            hint3 = font_normal.render("按 T 查看排名", True, (150, 150, 200))
            hint4 = font_normal.render("按 C 键更改玩家颜色", True, (150, 150, 200))
            screen.blit(hint1, (WIDTH // 2 - hint1.get_width() // 2, HEIGHT // 2 + 100))
            screen.blit(hint2, (WIDTH // 2 - hint2.get_width() // 2, HEIGHT // 2 + 140))
            screen.blit(hint3, (WIDTH // 2 - hint3.get_width() // 2, HEIGHT // 2 + 180))
            screen.blit(hint4, (WIDTH // 2 - hint4.get_width() // 2, HEIGHT // 2 + 220))


def main():
    game = AIDodger()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game.show_color_menu:
                        game.show_color_menu = False
                    elif game.show_ranking:
                        game.show_ranking = False
                    else:
                        running = False
                elif event.key == pygame.K_r:
                    if game.game_over or game.paused:
                        game = AIDodger()
                elif event.key == pygame.K_p:
                    if not game.show_ranking and not game.show_color_menu:
                        game.toggle_pause()
                elif event.key == pygame.K_SPACE:
                    if not game.show_ranking and not game.show_color_menu:
                        game.toggle_pause()
                elif event.key == pygame.K_t:
                    if not game.paused and not game.show_color_menu:
                        game.show_ranking = not game.show_ranking
                        if game.show_ranking:
                            game.ranking_scroll = 0
                elif event.key == pygame.K_c:
                    if not game.paused and not game.show_ranking and not game.game_over:
                        game.show_color_menu = not game.show_color_menu
                        if game.show_color_menu:
                            game.color_selection_pulse = 0
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if game.show_color_menu:
                        game.player_color = PLAYER_COLORS[game.player_color_index]
                        game.show_color_menu = False
                elif event.key == pygame.K_LEFT:
                    if game.show_color_menu:
                        game.player_color_index = (game.player_color_index - 1) % len(PLAYER_COLORS)
                elif event.key == pygame.K_RIGHT:
                    if game.show_color_menu:
                        game.player_color_index = (game.player_color_index + 1) % len(PLAYER_COLORS)
                elif event.key == pygame.K_UP:
                    if game.show_ranking:
                        game.ranking_scroll = max(0, game.ranking_scroll - 1)
                elif event.key == pygame.K_DOWN:
                    if game.show_ranking:
                        game.ranking_scroll += 1

        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()