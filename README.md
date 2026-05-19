# Cờ Caro AI — Minimax & Alpha-Beta Pruning

Chương trình chơi cờ Caro giữa người và máy tính.  
Máy sử dụng thuật toán **Minimax** và **Alpha-Beta Pruning** để chọn nước đi.  
Hỗ trợ chế độ **So sánh** — chạy cả hai thuật toán đồng thời và hiển thị kết quả song song.

---

## Cấu trúc project

```
source/
├── board.py          # Logic bàn cờ, hàm đánh giá, sinh nước đi
├── ai.py             # Thuật toán Minimax và Alpha-Beta
├── main.py           # Giao diện pygame, vòng lặp game
requirements.txt
README.md
```

---

## Yêu cầu hệ thống

- Python **3.10** trở lên
- pygame 2.x (xem `requirements.txt`)

---

## Cách cài đặt và chạy

### Bước 1 — Cài Python

Tải tại [https://python.org](https://python.org), chọn **Python 3.10+**.  
Khi cài trên Windows, **tick vào "Add Python to PATH"**.

### Bước 2 — Clone repository

```bash
git clone https://github.com/nguyenhoangkhanh19082005-collab/23021260_23021254_23021294_CaroAI.git
cd 23021260_23021254_23021294_CaroAI
```

Hoặc tải ZIP về và giải nén.

### Bước 3 — Cài thư viện

```bash
pip install -r requirements.txt
```

### Bước 4 — Chạy game

```bash
cd source
python main.py
```

---

## Cách chơi

| Hành động | Cách thực hiện |
|---|---|
| Đánh quân | Click vào ô trống trên bàn cờ |
| Ván mới | Click nút **Van moi** hoặc nhấn **R** |
| Chọn thuật toán | Click nút **Minimax** hoặc **Alpha-B** |
| Chế độ so sánh | Click nút **So sanh** — chạy cả hai thuật toán mỗi lượt |
| Đổi độ sâu | Click các nút **1 / 2 / 3 / 4** |

---

## Luật chơi

- Bàn cờ **10×10**.
- Người chơi là **X** (đỏ), máy là **O** (xanh).
- Thắng khi có **4 quân liên tiếp** theo hàng ngang / dọc / chéo.
- Không áp dụng luật chặn hai đầu.
- Bàn cờ đầy mà không ai thắng → **Hòa**.

---

## Thông tin hiển thị khi AI đánh

Sau mỗi nước đi của máy, bảng thống kê bên phải hiển thị:

| Thông tin | Ý nghĩa |
|---|---|
| Thuat toan | Thuật toán đang dùng |
| Do sau | Giới hạn độ sâu tìm kiếm |
| Trang thai xet | Số trạng thái đã duyệt |
| Thoi gian | Thời gian tính toán (ms) |
| Eval score | Điểm đánh giá trạng thái |
| Nuoc di | Tọa độ ô AI chọn |

Ở chế độ **So sánh**, bảng hiển thị song song kết quả của Minimax và Alpha-Beta, bao gồm tỉ lệ cắt nhánh (%).

---

> ⚠️ **Lưu ý:** Depth 4 + Minimax có thể mất 2–10 giây tùy trạng thái bàn cờ.  
> Nên dùng **Alpha-Beta** hoặc **So sánh** khi cần độ sâu cao.
