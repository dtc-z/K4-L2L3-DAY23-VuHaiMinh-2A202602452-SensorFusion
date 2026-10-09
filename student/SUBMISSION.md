# Báo cáo bài lab — Day 23 Sensor Fusion

## Thông tin học viên

- Họ tên: Vũ Hải Minh
- MSSV: 2A202602452
- Email: vhaiminh.2k5@gmail.com
- Link repo (fork): https://github.com/dtc-z/K4-L2L3-DAY23-VuHaiMinh-2A202602452-SensorFusion
- Commit hash nộp: "Done full"

## Tóm tắt kết quả

Bản demo thuyết trình độc lập: [`SENSOR_FUSION_DEMO.html`](../SENSOR_FUSION_DEMO.html).

- `fusion_mode`: `compare`; `frames`: `0–198` (199 frame); `segment`: `training_segment-1005081002024129653_5313_150_5333_150_with_camera_labels.tfrecord`; `seed`: `0`.
- Detection: precision **0.9701**, recall **0.7004**, TP **519**, FP **16**, FN **222**.
- LiDAR-only: RMSE **0.1503 m**, **502** matches, `sum_sq_err` **11.3369 m²**, **0** ghost track-frames, **239** missed GT frames, trung bình **2.5226** confirmed tracks/frame.
- LiDAR + camera: RMSE **0.1358 m**, **502** matches, `sum_sq_err` **9.2642 m²**, **0** ghost track-frames, **239** missed GT frames, trung bình **2.5226** confirmed tracks/frame.
- Chênh lệch: fused giảm RMSE **0.0144 m** (khoảng **9.6%**) trên cùng 502 matches. Số matches, ghosts, misses và confirmed tracks trung bình không đổi; trong lần chạy này camera cải thiện sai số vị trí của các track được ghép, không làm tăng số track/GT được ghép.

Các số trên lấy từ `student/artifacts/metrics.json`; log compare có 398 record (199 frame cho mỗi mode). Đã kiểm tra metrics khớp log và từng frame thỏa `matches + ghosts == confirmed`, `matches + misses == valid_gt`.

Camera trong lab nhận tâm hộp FRONT từ nhãn ground-truth rồi thêm nhiễu seeded; lab không chạy camera detector. Vì vậy kết quả fused này minh họa EKF camera update trong điều kiện đo mô phỏng, không chứng minh hiệu quả của một camera perception system độc lập.

## Giải thích Parts E–H

1. **Đo LiDAR và camera trong EKF:** LiDAR cung cấp vị trí 3D `(x, y, z)` theo đơn vị mét, với covariance `R` theo m². Camera cung cấp pixel `(u, v)`, với `R` theo pixel²; hàm chiếu pinhole dự đoán pixel từ trạng thái xe và Jacobian camera ánh xạ residual pixel về trạng thái 6D. Hai sensor dùng cùng trạng thái `(px, py, pz, vx, vy, vz)` nhưng có `h(x)`, `H` và đơn vị đo khác nhau.
2. **Gating Mahalanobis:** `d² = γᵀS⁻¹γ` so residual với độ bất định kết hợp của track và phép đo. Cổng χ² dùng số chiều phép đo để loại cặp không hợp lý trước greedy assignment; nhờ đó ngưỡng tính đến cả độ bất định, thay vì chỉ dùng khoảng cách Euclidean cố định.
3. **Track-then-fuse:** Runner dự đoán track một lần trong frame, association/update LiDAR trước, rồi association/update camera trên cùng manager và các track đó. Camera được xử lý sau LiDAR; đo camera mô phỏng từ nhãn FRONT có nhiễu.
4. **Calibration drift:** Sai lệch extrinsic/intrinsic tạo residual camera có bias có hệ thống so với `h(x)`. Innovation chuẩn hóa lớn hơn, dễ vượt gate; nếu vẫn được ghép, EKF có thể kéo vị trí track lệch theo một hướng.
5. **Sensor tường minh ở frame rỗng:** Danh sách phép đo rỗng không cho biết đó là lượt LiDAR hay camera. Manager cần sensor để áp dụng đúng lifecycle: miss LiDAR trong FOV giảm score, đo LiDAR không ghép có thể sinh track và LiDAR quản lý xóa track; camera chỉ hiệu chỉnh EKF, không chấm điểm, sinh hay xóa track.
6. **Vòng đời track:** Track mới có trạng thái `initialized`, score `1/window`. Hit LiDAR cộng `1/window` (tối đa 1); score lớn hơn `confirmed_threshold` thì thành `confirmed`, nếu chưa thì là `tentative`. Miss LiDAR trong FOV trừ `1/window`; confirmed vẫn giữ trạng thái confirmed sau miss nhưng bị xóa nếu score thấp hơn `delete_threshold`. Track chưa confirmed bị xóa khi score ≤ 0. Bất định ngang bị xóa nếu `Pxx` hoặc `Pyy` lớn hơn `max_P`; track ngoài FOV LiDAR không bị tính miss.

## Bonus

Không làm.

## Khai báo sử dụng AI

- Công cụ đã dùng (ChatGPT, Copilot, Claude, …): OpenAI Codex.
- Dùng cho phần nào: triển khai và rà soát lỗi có thể xảy ra Parts E–H, điều tra lỗi OpenMP trên Windows, đọc kết quả compare, soạn báo cáo và file demo HTML.
- Cách kiểm tra lại: chạy `student/tests` (**128 passed** khi bật UTF-8 trên Windows) và chạy Waymo compare đủ frame với `seed=0`; xác thực metrics/log theo record của runner.

## Checklist

- [x] Parts E–H đã implement; toàn bộ `student/tests` pass khi bật UTF-8 trên Windows.
- [x] Part A–D giữ nguyên.
- [x] Compare chạy với `seed=0`, `frame_start=0`, `frame_end=198`.
- [x] Đã tạo đủ sáu file metrics/log; metrics khớp log. (Chưa đánh dấu đã commit.)
- [x] Báo cáo và khai báo AI đã điền.
- [x] Không thêm dữ liệu Waymo, weights hay `paths.yaml` vào báo cáo.
- [x] Commit hash, commit artifacts, push và nộp LMS: Done