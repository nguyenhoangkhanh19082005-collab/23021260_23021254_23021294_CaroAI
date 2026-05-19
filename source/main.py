# main.py - Giao diện đồ họa bằng pygame và vòng lặp game chính

import sys
import threading
import pygame
from board import Board, EMPTY, PLAYER, AI, N
from ai import CaroAI

# ─── CẤU HÌNH GIAO DIỆN ──────────────────────────────────────────────────────

CELL        = 50          # Kích thước mỗi ô (px)
MARGIN      = 18          # Khoảng cách lề
PANEL_W     = 270         # Độ rộng bảng thông tin bên phải (tăng để chứa bảng so sánh)
FPS         = 60

BOARD_X     = MARGIN
BOARD_Y     = MARGIN
WIN_W       = MARGIN + N * CELL + MARGIN + PANEL_W + MARGIN
WIN_H       = MARGIN + N * CELL + MARGIN

# Bảng màu
BG          = (7,   7,  26)
BOARD_BG    = (14, 14,  40)
GRID_COL    = (26, 26,  52)
DOT_COL     = (40, 40,  80)
HOVER_COL   = (233, 69, 96, 35)
PANEL_BG    = (11, 11,  28)
BORDER_COL  = (26, 26,  52)

X_COL       = (233,  69,  96)   # Đỏ — người chơi
X_WIN_COL   = (255, 110, 140)
O_COL       = ( 76, 201, 240)   # Xanh — máy
O_WIN_COL   = (107, 228, 255)

TXT_BRIGHT  = (192, 192, 255)
TXT_MED     = (120, 128, 190)
TXT_DIM     = ( 60,  60, 120)
TXT_RED     = (233,  69,  96)
TXT_BLUE    = ( 76, 201, 240)
TXT_YELLOW  = (255, 209, 102)
TXT_GREEN   = (100, 220, 130)

BTN_ACTIVE  = ( 28,  28,  80)
BTN_IDLE    = ( 15,  15,  38)
BTN_CMP     = ( 28,  60,  28)   # Màu nút so sánh (xanh lá nhạt)


# ─── LỚP NÚT BẤM ─────────────────────────────────────────────────────────────

class Button:
    def __init__(self, x, y, w, h, label, font, color_active=None):
        self.rect         = pygame.Rect(x, y, w, h)
        self.label        = label
        self.font         = font
        self.active       = False
        self.hovered      = False
        self.color_active = color_active or BTN_ACTIVE

    def draw(self, screen):
        bg  = self.color_active if (self.active or self.hovered) else BTN_IDLE
        pygame.draw.rect(screen, bg, self.rect, border_radius=5)
        pygame.draw.rect(screen, BORDER_COL, self.rect, 1, border_radius=5)
        col = TXT_BRIGHT if self.active else (TXT_MED if self.hovered else TXT_DIM)
        surf = self.font.render(self.label, True, col)
        screen.blit(surf, surf.get_rect(center=self.rect.center))

    def update(self, mx, my):
        self.hovered = self.rect.collidepoint(mx, my)

    def clicked(self, mx, my):
        return self.rect.collidepoint(mx, my)


# ─── LỚP GAME CHÍNH ──────────────────────────────────────────────────────────

class CaroGame:
    # Chế độ thuật toán
    MODE_MINIMAX = 0
    MODE_AB      = 1
    MODE_COMPARE = 2   # Chạy cả hai, hiển thị so sánh

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Co Caro AI  —  Minimax & Alpha-Beta")
        self.clock  = pygame.time.Clock()

        # Fonts
        self.f_title = pygame.font.SysFont("Courier New", 17, bold=True)
        self.f_med   = pygame.font.SysFont("Courier New", 13)
        self.f_small = pygame.font.SysFont("Courier New", 11)

        # Trạng thái game
        self.board        = Board()
        self.ai_engine    = CaroAI()
        self.mode         = self.MODE_AB   # Mặc định Alpha-Beta
        self.depth        = 3
        self.status       = "playing"      # playing | player_win | ai_win | draw
        self.ai_first     = False          # Biến lưu trạng thái Máy đi trước hay Người đi trước
        self.player_turn  = True
        self.computing    = False
        self.stats        = None           # Thống kê nước đi AI gần nhất
        self.compare_stats = None          # Kết quả so sánh Minimax vs AB
        self.win_line     = None
        self.last_ai      = None
        self.move_log     = []
        self.hover_cell   = None

        self._build_buttons()

    # ─── Khởi tạo nút bấm ────────────────────────────────────────────────────

    def _build_buttons(self):
        px = BOARD_X + N * CELL + MARGIN * 2
        f  = self.f_small

        # Chọn chế độ thuật toán (3 nút)
        btn_w = 72
        self.btn_mm  = Button(px,            32, btn_w, 25, "Minimax",   f)
        self.btn_ab  = Button(px + btn_w + 4, 32, btn_w, 25, "Alpha-B",  f)
        self.btn_cmp = Button(px + (btn_w+4)*2, 32, btn_w, 25, "So sanh", f,
                              color_active=BTN_CMP)
        self.btn_ab.active = True

        # Chọn độ sâu
        self.btn_depth = [Button(px + 60 + i * 33, 68, 28, 25, str(i + 1), f)
                          for i in range(4)]
        self.btn_depth[self.depth - 1].active = True

        # Chọn người đi trước
        self.btn_first_p = Button(px + 70, 104, 85, 25, "Nguoi (X)", f)
        self.btn_first_a = Button(px + 159, 104, 85, 25, "May (O)", f)
        self.btn_first_p.active = True

        # Ván mới
        self.btn_new = Button(px, WIN_H - 48, PANEL_W - MARGIN, 32,
                              "Van moi  [R]", self.f_med)

        self._all_buttons = ([self.btn_mm, self.btn_ab, self.btn_cmp, self.btn_new,
                              self.btn_first_p, self.btn_first_a]
                             + self.btn_depth)

    # ─── Reset game ───────────────────────────────────────────────────────────

    def reset(self):
        if self.computing:
            return
        self.board         = Board()
        self.status        = "playing"
        self.stats         = None
        self.compare_stats = None
        self.win_line      = None
        self.last_ai       = None
        self.move_log      = []

        # Nếu chọn Máy đi trước, kích hoạt AI chạy ngay lập tức
        if self.ai_first:
            self.player_turn = False
            self.computing   = True
            t = threading.Thread(target=self._ai_move_thread, daemon=True)
            t.start()
        else:
            self.player_turn = True
            self.computing   = False

    # ─── Xử lý sự kiện ───────────────────────────────────────────────────────

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()
                
                # KHÔI PHỤC LẠI: Phím SPACE để ép AI tính toán nước đi
                if event.key == pygame.K_SPACE:
                    if not self.computing and self.status == "playing":
                        self.player_turn = False
                        self.computing = True
                        t = threading.Thread(target=self._ai_move_thread, daemon=True)
                        t.start()

            if event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                for btn in self._all_buttons:
                    btn.update(mx, my)
                c = (mx - BOARD_X) // CELL
                r = (my - BOARD_Y) // CELL
                self.hover_cell = (r, c) if (0 <= r < N and 0 <= c < N) else None

            # KHÔI PHỤC LẠI: Phân biệt Chuột trái và Chuột phải
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if event.button == 1:
                    # Chuột trái: Đánh quân X hoặc bấm nút giao diện
                    self._handle_click(mx, my)
                elif event.button == 3:
                    # Chuột phải: Trực tiếp đặt quân O (Máy) lên bàn cờ
                    if (BOARD_X <= mx < BOARD_X + N * CELL and BOARD_Y <= my < BOARD_Y + N * CELL):
                        c = (mx - BOARD_X) // CELL
                        r = (my - BOARD_Y) // CELL
                        # Chỉ cho phép đặt khi ô trống và AI không bận tính toán
                        if self.board.grid[r][c] == EMPTY and not self.computing:
                            self.board.place(r, c, AI)

    def _handle_click(self, mx, my):
        # Click lên bàn cờ
        if (BOARD_X <= mx < BOARD_X + N * CELL and
                BOARD_Y <= my < BOARD_Y + N * CELL):
            c = (mx - BOARD_X) // CELL
            r = (my - BOARD_Y) // CELL
            self._player_move(r, c)
            return

        # Tương tác với các nút bấm (Chỉ khi AI không bận tính toán)
        if not self.computing:
            # Nhóm nút thuật toán
            if self.btn_mm.clicked(mx, my):
                self.mode = self.MODE_MINIMAX
                self.btn_mm.active  = True
                self.btn_ab.active  = False
                self.btn_cmp.active = False
            if self.btn_ab.clicked(mx, my):
                self.mode = self.MODE_AB
                self.btn_mm.active  = False
                self.btn_ab.active  = True
                self.btn_cmp.active = False
            if self.btn_cmp.clicked(mx, my):
                self.mode = self.MODE_COMPARE
                self.btn_mm.active  = False
                self.btn_ab.active  = False
                self.btn_cmp.active = True

            # Nhóm nút lượt đi trước
            if self.btn_first_p.clicked(mx, my) and self.ai_first:
                self.ai_first = False
                self.btn_first_p.active = True
                self.btn_first_a.active = False
                self.reset()  # Reset lại game ngay khi đổi người đi trước
            if self.btn_first_a.clicked(mx, my) and not self.ai_first:
                self.ai_first = True
                self.btn_first_p.active = False
                self.btn_first_a.active = True
                self.reset()

            # Nút độ sâu
            for i, btn in enumerate(self.btn_depth):
                if btn.clicked(mx, my):
                    self.depth = i + 1
                    for b in self.btn_depth:
                        b.active = False
                    btn.active = True

        # Nút ván mới
        if self.btn_new.clicked(mx, my):
            self.reset()

    # ─── Người chơi đánh ─────────────────────────────────────────────────────

    def _player_move(self, r, c):
        if (not self.player_turn or self.status != "playing"
                or self.board.grid[r][c] != EMPTY or self.computing):
            return

        self.board.place(r, c, PLAYER)

        if self.board.check_win(r, c, PLAYER):
            self.win_line    = self.board.get_win_line(r, c, PLAYER)
            self.status      = "player_win"
            return
        if self.board.is_full():
            self.status = "draw"
            return

        # TẠM THỜI TẮT CHUYỂN LƯỢT CHO AI ĐỂ RẢNH TAY SETUP BÀN CỜ BẰNG CHUỘT TRÁI
        # Nếu bạn muốn chơi bình thường (AI tự đánh lại sau khi bạn click chuột trái),
        # hãy bỏ comment 4 dòng bên dưới.
        # Nhưng để test, ta tạm thời tắt đi. Bạn sẽ ấn SPACE để gọi AI.
        
        # self.player_turn = False
        # self.computing   = True
        # t = threading.Thread(target=self._ai_move_thread, daemon=True)
        # t.start()

    # ─── AI tính nước đi (chạy trên thread riêng) ────────────────────────────

    def _ai_move_thread(self):
        self.compare_stats = None

        if self.mode == self.MODE_COMPARE:
            # Chạy cả hai thuật toán để so sánh
            combined = self.ai_engine.find_best_move_both(self.board, self.depth)
            self.compare_stats = combined
            result = combined["ab"]   # Dùng nước đi của Alpha-Beta
        else:
            use_ab = (self.mode == self.MODE_AB)
            result = self.ai_engine.find_best_move(self.board, use_ab, self.depth)

        if result["move"] is None:
            self.status    = "draw"
            self.computing = False
            return

        r, c = result["move"]
        self.board.place(r, c, AI)
        self.last_ai = (r, c)

        algo_name = {
            self.MODE_MINIMAX: "Minimax",
            self.MODE_AB:      "Alpha-Beta",
            self.MODE_COMPARE: "Alpha-Beta*",
        }[self.mode]

        info = {**result, "depth": self.depth, "algo": algo_name}
        self.stats    = info
        self.move_log = (self.move_log + [info])[-8:]

        if self.board.check_win(r, c, AI):
            self.win_line = self.board.get_win_line(r, c, AI)
            self.status   = "ai_win"
        elif self.board.is_full():
            self.status = "draw"
        else:
            self.player_turn = True

        self.computing = False

    # ─── Vẽ bàn cờ ───────────────────────────────────────────────────────────

    def _draw_board(self):
        board_rect = pygame.Rect(BOARD_X - 2, BOARD_Y - 2,
                                 N * CELL + 4, N * CELL + 4)
        pygame.draw.rect(self.screen, BOARD_BG, board_rect, border_radius=4)

        for i in range(N + 1):
            pygame.draw.line(self.screen, GRID_COL,
                             (BOARD_X + i * CELL, BOARD_Y),
                             (BOARD_X + i * CELL, BOARD_Y + N * CELL))
            pygame.draw.line(self.screen, GRID_COL,
                             (BOARD_X, BOARD_Y + i * CELL),
                             (BOARD_X + N * CELL, BOARD_Y + i * CELL))

        for dr, dc in [(2, 2), (2, 7), (7, 2), (7, 7), (4, 4)]:
            pygame.draw.circle(self.screen, DOT_COL,
                               (BOARD_X + dc * CELL + CELL // 2,
                                BOARD_Y + dr * CELL + CELL // 2), 3)

        if (self.hover_cell and self.player_turn
                and self.status == "playing" and not self.computing):
            hr, hc = self.hover_cell
            if self.board.grid[hr][hc] == EMPTY:
                s = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                s.fill(HOVER_COL)
                self.screen.blit(s, (BOARD_X + hc * CELL, BOARD_Y + hr * CELL))

        win_set = set(self.win_line) if self.win_line else set()

        for r in range(N):
            for c in range(N):
                cell = self.board.grid[r][c]
                if cell == EMPTY:
                    continue
                cx = BOARD_X + c * CELL + CELL // 2
                cy = BOARD_Y + r * CELL + CELL // 2
                is_win  = (r, c) in win_set
                is_last = self.last_ai == (r, c)

                if cell == PLAYER:
                    col = X_WIN_COL if is_win else X_COL
                    if is_win:
                        s = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                        pygame.draw.circle(s, (*X_COL, 40),
                                           (CELL // 2, CELL // 2), CELL // 2 - 3)
                        self.screen.blit(s, (BOARD_X + c * CELL, BOARD_Y + r * CELL))
                    w = 3 if is_win else 2
                    pygame.draw.line(self.screen, col,
                                     (cx - 14, cy - 14), (cx + 14, cy + 14), w)
                    pygame.draw.line(self.screen, col,
                                     (cx + 14, cy - 14), (cx - 14, cy + 14), w)

                elif cell == AI:
                    col = O_WIN_COL if is_win else O_COL
                    if is_win:
                        s = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                        pygame.draw.circle(s, (*O_COL, 40),
                                           (CELL // 2, CELL // 2), CELL // 2 - 3)
                        self.screen.blit(s, (BOARD_X + c * CELL, BOARD_Y + r * CELL))
                    if is_last:
                        pygame.draw.circle(self.screen, O_COL,
                                           (cx, cy), CELL // 2 - 4, 1)
                    w = 3 if is_win else 2
                    pygame.draw.circle(self.screen, col, (cx, cy), 14, w)
                    if is_last:
                        pygame.draw.circle(self.screen, O_COL, (cx, cy), 4)

    # ─── Vẽ panel bên phải ───────────────────────────────────────────────────

    def _draw_panel(self):
        px = BOARD_X + N * CELL + MARGIN * 2

        # Tiêu đề
        self.screen.blit(
            self.f_title.render("CO CARO AI", True, TXT_BRIGHT),
            (px, MARGIN - 4))

        # Nút thuật toán
        self.btn_mm.draw(self.screen)
        self.btn_ab.draw(self.screen)
        self.btn_cmp.draw(self.screen)

        # Nút độ sâu
        self.screen.blit(
            self.f_small.render("Do sau:", True, TXT_DIM),
            (px, 74))
        for btn in self.btn_depth:
            btn.draw(self.screen)

        # Nút lượt đi trước
        self.screen.blit(
            self.f_small.render("Di truoc:", True, TXT_DIM),
            (px, 110))
        self.btn_first_p.draw(self.screen)
        self.btn_first_a.draw(self.screen)

        # Trạng thái lượt chơi
        cy = 145
        if self.status == "playing":
            if self.computing:
                msg = "May dang tinh..."
                col = TXT_YELLOW
            elif self.player_turn:
                msg = "Luot cua ban (X)"
                col = X_COL
            else:
                msg = ""
                col = TXT_DIM
        elif self.status == "player_win":
            msg, col = "Ban thang!", X_COL
        elif self.status == "ai_win":
            msg, col = "May thang!", O_COL
        else:
            msg, col = "Hoa!", TXT_YELLOW

        self.screen.blit(self.f_med.render(msg, True, col), (px, cy))
        cy += 20

        # ── Bảng thống kê (1 thuật toán) ─────────────────────────────────────
        if self.stats and self.mode != self.MODE_COMPARE:
            card = pygame.Rect(px, cy, PANEL_W - MARGIN, 115)
            pygame.draw.rect(self.screen, PANEL_BG, card, border_radius=5)
            pygame.draw.rect(self.screen, BORDER_COL, card, 1, border_radius=5)

            self.screen.blit(
                self.f_small.render("THONG KE NUOC DI", True, TXT_DIM),
                (px + 8, cy + 6))

            rows = [
                ("Thuat toan",     self.stats["algo"]),
                ("Do sau",         str(self.stats["depth"])),
                ("Trang thai xet", f"{self.stats['states']:,}"),
                ("Thoi gian",      f"{self.stats['time']:.1f} ms"),
                ("Eval score",     str(self.stats["value"])),
                ("Nuoc di",        f"({self.stats['move'][0]+1},{self.stats['move'][1]+1})"),
            ]
            for i, (k, v) in enumerate(rows):
                ry = cy + 24 + i * 15
                ev = (O_COL if (k == "Eval score" and self.stats["value"] > 0)
                      else X_COL if (k == "Eval score" and self.stats["value"] < 0)
                      else TXT_BRIGHT)
                self.screen.blit(self.f_small.render(k, True, TXT_DIM), (px + 8, ry))
                vs = self.f_small.render(v, True, ev)
                self.screen.blit(vs, (px + PANEL_W - MARGIN - vs.get_width() - 4, ry))
            cy += 120

        # ── Bảng so sánh Minimax vs Alpha-Beta ───────────────────────────────
        elif self.compare_stats and self.mode == self.MODE_COMPARE:
            mm = self.compare_stats["mm"]
            ab = self.compare_stats["ab"]
            card_h = 130
            card = pygame.Rect(px, cy, PANEL_W - MARGIN, card_h)
            pygame.draw.rect(self.screen, PANEL_BG, card, border_radius=5)
            pygame.draw.rect(self.screen, BORDER_COL, card, 1, border_radius=5)

            # Header
            self.screen.blit(
                self.f_small.render("SO SANH MINIMAX vs ALPHA-BETA", True, TXT_DIM),
                (px + 8, cy + 6))

            col_x = [px + 8, px + 108, px + 190]
            hdr_y = cy + 20
            self.screen.blit(self.f_small.render("Chi so",      True, TXT_DIM), (col_x[0], hdr_y))
            self.screen.blit(self.f_small.render("Minimax",     True, TXT_MED), (col_x[1], hdr_y))
            self.screen.blit(self.f_small.render("Alpha-B",     True, TXT_BLUE),(col_x[2], hdr_y))

            # Kẻ đường gạch
            pygame.draw.line(self.screen, BORDER_COL,
                             (px + 8, hdr_y + 13), (px + PANEL_W - MARGIN - 8, hdr_y + 13))

            rows = [
                ("Trang thai", f"{mm['states']:,}", f"{ab['states']:,}"),
                ("Thoi gian",  f"{mm['time']:.0f}ms", f"{ab['time']:.0f}ms"),
                ("Eval",       str(mm["value"]),  str(ab["value"])),
                ("Nuoc di",
                 f"({mm['move'][0]+1},{mm['move'][1]+1})",
                 f"({ab['move'][0]+1},{ab['move'][1]+1})"),
            ]
            for i, (k, v_mm, v_ab) in enumerate(rows):
                ry = hdr_y + 17 + i * 16
                self.screen.blit(self.f_small.render(k,    True, TXT_DIM), (col_x[0], ry))
                self.screen.blit(self.f_small.render(v_mm, True, TXT_MED), (col_x[1], ry))
                self.screen.blit(self.f_small.render(v_ab, True, TXT_BLUE),(col_x[2], ry))

            # Tỉ lệ cắt nhánh
            if mm["states"] > 0:
                pct = (1 - ab["states"] / mm["states"]) * 100
                pct_s = f"Cat nhanh: {pct:.1f}%"
                pct_col = TXT_GREEN if pct > 0 else TXT_RED
                self.screen.blit(self.f_small.render(pct_s, True, pct_col),
                                 (px + 8, hdr_y + 17 + len(rows) * 16 + 2))
            cy += card_h + 5

        # ── Lịch sử nước đi AI ────────────────────────────────────────────────
        if self.move_log:
            log_h = len(self.move_log) * 17 + 26
            # Đảm bảo không vượt quá vùng hiển thị
            max_log_h = WIN_H - cy - 60
            if log_h > max_log_h:
                log_h = max_log_h
            if log_h > 40:
                log_card = pygame.Rect(px, cy, PANEL_W - MARGIN, log_h)
                pygame.draw.rect(self.screen, PANEL_BG, log_card, border_radius=5)
                pygame.draw.rect(self.screen, BORDER_COL, log_card, 1, border_radius=5)

                self.screen.blit(
                    self.f_small.render(f"LICH SU AI ({len(self.move_log)} nuoc)",
                                        True, TXT_DIM),
                    (px + 8, cy + 6))

                n = len(self.move_log)
                visible_rows = (log_h - 26) // 17
                shown = self.move_log[-visible_rows:]
                for i, s in enumerate(shown):
                    ry = cy + 24 + i * 17
                    if ry + 14 > cy + log_h:
                        break
                    alpha = 80 + int(175 * (i + 1) / max(len(shown), 1))
                    c_fade = tuple(int(v * alpha / 255) for v in O_COL)
                    t1 = self.f_small.render(f"({s['move'][0]+1},{s['move'][1]+1})", True, c_fade)
                    t2 = self.f_small.render(f"{s['states']:>7,}", True, TXT_DIM)
                    t3 = self.f_small.render(f"{s['time']:>5.0f}ms", True, (55, 55, 100))
                    self.screen.blit(t1, (px + 5,   ry))
                    self.screen.blit(t2, (px + 70,  ry))
                    self.screen.blit(t3, (px + 155, ry))

        # ── Chú thích ký hiệu ─────────────────────────────────────────────────
        leg_y = WIN_H - 88
        pygame.draw.line(self.screen, X_COL, (px, leg_y + 6), (px + 18, leg_y + 6), 2)
        pygame.draw.line(self.screen, X_COL, (px + 9, leg_y - 2), (px + 9, leg_y + 14), 2)
        self.screen.blit(
            self.f_small.render("Ban (X)  — di truoc", True, TXT_DIM),
            (px + 26, leg_y))
        pygame.draw.circle(self.screen, O_COL, (px + 9, leg_y + 28), 8, 2)
        self.screen.blit(
            self.f_small.render("May (O)  — AI", True, TXT_DIM),
            (px + 26, leg_y + 20))

        # Chú thích chế độ so sánh
        if self.mode == self.MODE_COMPARE:
            self.screen.blit(
                self.f_small.render("* So sanh: ca 2 thuat toan chay", True, TXT_GREEN),
                (px, leg_y + 42))
        
        # Chú thích cách test
        self.screen.blit(
            self.f_small.render("* MEO TEST:", True, TXT_YELLOW),
            (px, leg_y + 56))
        self.screen.blit(
            self.f_small.render("  1. Chuot phai: Xep O", True, TXT_DIM),
            (px, leg_y + 70))
        self.screen.blit(
            self.f_small.render("  2. Phim SPACE: Goi AI", True, TXT_DIM),
            (px, leg_y + 84))

        # ── Nút ván mới ───────────────────────────────────────────────────────
        self.btn_new.active = False
        self.btn_new.draw(self.screen)

    # ─── Vòng lặp chính ──────────────────────────────────────────────────────

    def run(self):
        while True:
            self.handle_events()
            self.screen.fill(BG)
            self._draw_board()
            self._draw_panel()
            pygame.display.flip()
            self.clock.tick(FPS)


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    game = CaroGame()
    game.run()
