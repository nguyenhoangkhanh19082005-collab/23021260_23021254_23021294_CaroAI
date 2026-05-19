# board.py - Quản lý bàn cờ và logic trò chơi

EMPTY  = 0
PLAYER = 1   # Người chơi (X)
AI     = 2   # Máy tính (O)
N      = 10  # Kích thước bàn cờ 10x10
WIN    = 4   # Số quân liên tiếp để thắng

# Bốn hướng kiểm tra: ngang, dọc, chéo chính, chéo phụ
DIRS = [(0, 1), (1, 0), (1, 1), (1, -1)]


class Board:
    def __init__(self):
        # Bàn cờ là mảng 2D, 0=trống, 1=người, 2=máy
        self.grid = [[EMPTY] * N for _ in range(N)]

    def clone(self):
        """Tạo bản sao bàn cờ (dùng trong thuật toán tìm kiếm)."""
        b = Board()
        b.grid = [row[:] for row in self.grid]
        return b

    def place(self, r, c, player):
        """Đặt quân tại ô (r, c)."""
        self.grid[r][c] = player

    def remove(self, r, c):
        """Xoá quân tại ô (r, c) — dùng khi backtrack trong minimax."""
        self.grid[r][c] = EMPTY

    def in_bounds(self, r, c):
        return 0 <= r < N and 0 <= c < N

    def is_full(self):
        return all(self.grid[r][c] != EMPTY for r in range(N) for c in range(N))

    # ─── Kiểm tra thắng ──────────────────────────────────────────────────────

    def check_win(self, r, c, player):
        """Kiểm tra xem nước đi tại (r,c) có tạo WIN quân liên tiếp không."""
        for dr, dc in DIRS:
            count = 1
            # Đếm về phía dương
            for i in range(1, N):
                nr, nc = r + dr * i, c + dc * i
                if not self.in_bounds(nr, nc) or self.grid[nr][nc] != player:
                    break
                count += 1
            # Đếm về phía âm
            for i in range(1, N):
                nr, nc = r - dr * i, c - dc * i
                if not self.in_bounds(nr, nc) or self.grid[nr][nc] != player:
                    break
                count += 1
            if count >= WIN:
                return True
        return False

    def get_win_line(self, r, c, player):
        """Trả về danh sách đúng WIN ô tạo thành chuỗi thắng (để highlight)."""
        for dr, dc in DIRS:
            cells = [(r, c)]
            for i in range(1, N):
                nr, nc = r + dr * i, c + dc * i
                if not self.in_bounds(nr, nc) or self.grid[nr][nc] != player:
                    break
                cells.append((nr, nc))
            for i in range(1, N):
                nr, nc = r - dr * i, c - dc * i
                if not self.in_bounds(nr, nc) or self.grid[nr][nc] != player:
                    break
                cells.insert(0, (nr, nc))
            if len(cells) >= WIN:
                # Tìm vị trí (r,c) trong cells rồi lấy đúng WIN ô
                idx = cells.index((r, c))
                start = max(0, idx - (WIN - 1))
                start = min(start, len(cells) - WIN)
                return cells[start: start + WIN]
        return None

    # ─── Sinh nước đi ────────────────────────────────────────────────────────

    def get_candidates(self):
        """
        Chỉ sinh nước đi trong vùng bán kính 2 quanh các quân đã đánh.
        Giảm mạnh không gian tìm kiếm so với xét toàn bộ ô trống.
        """
        candidates = set()
        for r in range(N):
            for c in range(N):
                if self.grid[r][c] != EMPTY:
                    for dr in range(-2, 3):
                        for dc in range(-2, 3):
                            nr, nc = r + dr, c + dc
                            if self.in_bounds(nr, nc) and self.grid[nr][nc] == EMPTY:
                                candidates.add((nr, nc))
        if not candidates:
            # Bàn cờ trống → đánh trung tâm
            candidates.add((N // 2, N // 2))
        return list(candidates)

    # ─── Hàm đánh giá trạng thái ─────────────────────────────────────────────

    def evaluate(self):
        """
        Tính điểm cho trạng thái hiện tại (dùng khi đạt giới hạn độ sâu).
        Quét tất cả cửa sổ WIN ô theo 4 hướng và tính điểm theo chuỗi quân.

        Điểm dương: lợi cho máy (AI).
        Điểm âm:    lợi cho người (PLAYER).

        Thang điểm cân bằng:
          - 3 quân AI / PLAYER được ưu tiên tương đương nhau để AI biết chặn.
          - Phòng thủ (chặn 3) được điểm cao hơn tấn công (tạo 2) để AI không bỏ qua nguy hiểm.
        """
        score = 0
        for r in range(N):
            for c in range(N):
                for dr, dc in DIRS:
                    # Kiểm tra cửa sổ WIN ô bắt đầu từ (r, c) theo hướng (dr, dc)
                    er, ec = r + dr * (WIN - 1), c + dc * (WIN - 1)
                    if not self.in_bounds(er, ec):
                        continue
                    ai_cnt = pl_cnt = 0
                    for i in range(WIN):
                        v = self.grid[r + dr * i][c + dc * i]
                        if v == AI:
                            ai_cnt += 1
                        elif v == PLAYER:
                            pl_cnt += 1

                    # Cửa sổ thuần máy (không có quân người)
                    if pl_cnt == 0:
                        if ai_cnt == 4:   score += 100_000
                        elif ai_cnt == 3: score +=   1_000
                        elif ai_cnt == 2: score +=     100
                        elif ai_cnt == 1: score +=      10

                    # Cửa sổ thuần người (không có quân máy) → ưu tiên chặn
                    if ai_cnt == 0:
                        if pl_cnt == 4:   score -= 100_000
                        elif pl_cnt == 3: score -=   5_000   # Chặn mạnh hơn tấn công
                        elif pl_cnt == 2: score -=     500
                        elif pl_cnt == 1: score -=      10

        return score
