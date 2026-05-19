# ai.py - Thuật toán Minimax và Alpha-Beta Pruning

import math
import time
from board import Board, EMPTY, PLAYER, AI, WIN


class CaroAI:
    def __init__(self):
        self.states_count = 0   # Số trạng thái đã xét (reset mỗi lần tìm nước đi)

    # ─── MINIMAX ─────────────────────────────────────────────────────────────

    def minimax(self, board: Board, depth: int, is_max: bool,
                last_r, last_c, max_depth: int) -> int:
        """
        Thuật toán Minimax có giới hạn độ sâu.

        Args:
            board:     Bàn cờ hiện tại.
            depth:     Độ sâu hiện tại trong cây tìm kiếm.
            is_max:    True = lượt AI (maximizer), False = lượt người (minimizer).
            last_r/c:  Ô vừa đánh (để kiểm tra thắng nhanh).
            max_depth: Giới hạn độ sâu tìm kiếm.

        Returns:
            Giá trị đánh giá của trạng thái.
        """
        self.states_count += 1

        # Kiểm tra trạng thái kết thúc do nước đi vừa rồi
        if last_r is not None:
            last_player = PLAYER if is_max else AI  # người vừa đánh trước đó
            if board.check_win(last_r, last_c, last_player):
                # Thắng sớm hơn (depth nhỏ hơn) → giá trị lớn hơn
                return (-1 if is_max else 1) * (100_000 + max_depth - depth)

        # Đạt giới hạn độ sâu hoặc bàn cờ đầy → dùng hàm đánh giá
        if depth >= max_depth or board.is_full():
            return board.evaluate()

        moves = board.get_candidates()

        if is_max:
            # Lượt AI: chọn giá trị lớn nhất
            best = -math.inf
            for r, c in moves:
                board.place(r, c, AI)
                val = self.minimax(board, depth + 1, False, r, c, max_depth)
                board.remove(r, c)
                best = max(best, val)
            return best
        else:
            # Lượt người: chọn giá trị nhỏ nhất
            best = math.inf
            for r, c in moves:
                board.place(r, c, PLAYER)
                val = self.minimax(board, depth + 1, True, r, c, max_depth)
                board.remove(r, c)
                best = min(best, val)
            return best

    # ─── ALPHA-BETA PRUNING ───────────────────────────────────────────────────

    def alpha_beta(self, board: Board, depth: int, alpha: float, beta: float,
                   is_max: bool, last_r, last_c, max_depth: int) -> int:
        """
        Minimax cải tiến bằng Alpha-Beta Pruning.

        Args:
            alpha: Giá trị tốt nhất hiện tại của MAX (AI).
            beta:  Giá trị tốt nhất hiện tại của MIN (người).
            Cắt nhánh khi beta <= alpha.
        """
        self.states_count += 1

        if last_r is not None:
            last_player = PLAYER if is_max else AI
            if board.check_win(last_r, last_c, last_player):
                return (-1 if is_max else 1) * (100_000 + max_depth - depth)

        if depth >= max_depth or board.is_full():
            return board.evaluate()

        moves = board.get_candidates()

        if is_max:
            best = -math.inf
            for r, c in moves:
                board.place(r, c, AI)
                val = self.alpha_beta(board, depth + 1, alpha, beta,
                                      False, r, c, max_depth)
                board.remove(r, c)
                best = max(best, val)
                alpha = max(alpha, best)
                if beta <= alpha:   # ✂ Cắt nhánh beta
                    break
            return best
        else:
            best = math.inf
            for r, c in moves:
                board.place(r, c, PLAYER)
                val = self.alpha_beta(board, depth + 1, alpha, beta,
                                      True, r, c, max_depth)
                board.remove(r, c)
                best = min(best, val)
                beta = min(beta, best)
                if beta <= alpha:   # ✂ Cắt nhánh alpha
                    break
            return best

    # ─── TÌM NƯỚC ĐI TỐT NHẤT ───────────────────────────────────────────────

    def find_best_move(self, board: Board, use_ab: bool, max_depth: int) -> dict:
        """
        Duyệt tất cả nước đi hợp lệ ở tầng gốc, chọn nước đi tốt nhất cho AI.

        Args:
            board:     Bàn cờ hiện tại (sẽ không bị thay đổi).
            use_ab:    True = dùng Alpha-Beta, False = dùng Minimax thuần.
            max_depth: Giới hạn độ sâu.

        Returns:
            dict gồm: move, value, states, time
        """
        self.states_count = 0
        moves = board.get_candidates()
        best_move = None
        best_val  = -math.inf
        t0 = time.time()

        # Làm việc trên bản sao để không ảnh hưởng bàn cờ thật
        b = board.clone()

        for r, c in moves:
            b.place(r, c, AI)
            if use_ab:
                val = self.alpha_beta(b, 1, -math.inf, math.inf,
                                      False, r, c, max_depth)
            else:
                val = self.minimax(b, 1, False, r, c, max_depth)
            b.remove(r, c)

            if val > best_val or best_move is None:
                best_val  = val
                best_move = (r, c)

        elapsed_ms = (time.time() - t0) * 1000
        return {
            "move":   best_move,
            "value":  best_val,
            "states": self.states_count,
            "time":   elapsed_ms,
        }

    def find_best_move_both(self, board: Board, max_depth: int) -> dict:
        """
        Chạy CẢ HAI thuật toán Minimax và Alpha-Beta trên cùng một trạng thái.
        Dùng để so sánh hiệu quả theo yêu cầu Level 2 của đề bài.

        Returns:
            dict gồm: move (Alpha-Beta), mm (kết quả Minimax), ab (kết quả Alpha-Beta)
        """
        # Chạy Minimax
        result_mm = self.find_best_move(board, use_ab=False, max_depth=max_depth)
        result_mm["algo"] = "Minimax"

        # Chạy Alpha-Beta
        result_ab = self.find_best_move(board, use_ab=True, max_depth=max_depth)
        result_ab["algo"] = "Alpha-Beta"

        # Dùng nước đi của Alpha-Beta (hiệu quả hơn, cùng kết quả)
        return {
            "move": result_ab["move"],
            "mm":   result_mm,
            "ab":   result_ab,
        }
