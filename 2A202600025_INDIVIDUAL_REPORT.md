# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Đặng Tuấn Anh
- **Student ID**: 2A202600025
- **Date**: 06-04-2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/tools/get_hotel_details.py`
- **Code Highlights**: 
  Tôi đã xây dựng công cụ truy xuất thông tin chi tiết khách sạn từ một Mock Database. Điểm nhấn trong code là cách xử lý chuỗi đầu vào (chuẩn hóa ID) và đặc biệt là cơ chế tự sửa lỗi (self-correction mechanism) cho ReAct Agent khi nhập sai ID:
  ```python
  normalized_id = hotel_id.strip().upper()
  hotel = HOTEL_DETAILS.get(normalized_id)

  if not hotel:
      return (
          f"No detail data found for hotel_id={normalized_id}. "
          f"Available IDs: {', '.join(HOTEL_DETAILS.keys())}."
      )
  ```
- **Documentation**: Công cụ `get_hotel_details` cung cấp cho ReAct Agent khả năng tra cứu các thông tin cụ thể (chính sách hủy phòng, tiện ích, loại phòng, giá cả). Thay vì Agent phải tự bịa ra thông tin (hallucinate), nó có thể dùng công cụ này với input là `hotel_id` (ví dụ: "HCM001") để lấy data thực tế dạng text đã được format thân thiện với LLM, từ đó trả lời chính xác câu hỏi của người dùng.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Agent bị kẹt trong vòng lặp vô hạn (infinite loop) vì liên tục truyền tên khách sạn thay vì mã `hotel_id` vào tool. (Ví dụ: Agent gọi `get_hotel_details(hotel_id="Saigon Grand Hotel")` thay vì `HCM001`).
- **Log Source**: `logs/2026-04-06.log`
  ```text
  Thought: I need to find the cancellation policy for Saigon Grand Hotel.
  Action: get_hotel_details
  Action Input: Saigon Grand Hotel
  Observation: No detail data found for hotel_id=SAIGON GRAND HOTEL.
  Thought: Let me try again with the city.
  Action: get_hotel_details
  Action Input: Ho Chi Minh
  ...
  ```
- **Diagnosis**: LLM không hiểu rõ định dạng đầu vào bắt buộc của tham số `hotel_id`. Nó bị nhầm lẫn giữa "Tên khách sạn" và "Mã định danh khách sạn". Do hệ thống prompt và mô tả công cụ (tool description) ban đầu chưa đủ chặt chẽ.
- **Solution**: 
  1. Tôi đã cập nhật lại docstring của hàm để làm rõ ví dụ: `"hotel identifier (for example: HCM001, HAN002, DAD003)"`.
  2. Thêm cơ chế phản hồi thông minh trong code (như đã nêu ở phần I) để báo cho Agent biết các ID hợp lệ là gì: `Available IDs: HCM001, HAN002, DAD003`. Nhờ Observation này, ở bước Thought tiếp theo, Agent đã tự nhận ra sai lầm và chọn đúng ID.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Khối `Thought` giúp Agent lập kế hoạch từng bước rất tốt. Ví dụ: Khi user hỏi *"Khách sạn nào ở HCM có hồ bơi và giá bao nhiêu?"*, một Chatbot thông thường có thể chỉ đoán bừa. Nhưng ReAct Agent sẽ dùng `Thought` để phân tích: Bước 1 tìm khách sạn ở HCM -> Bước 2 dùng `get_hotel_details("HCM001")` để check xem tiện ích (amenities) có `pool: True` hay không -> Bước 3 tổng hợp giá và trả lời.
2.  **Reliability**: Agent hoạt động *tệ hơn* Chatbot thông thường trong các trường hợp câu hỏi mang tính giao tiếp thông thường (chào hỏi, tán gẫu). Trong những lúc đó, Agent đôi khi lạm dụng việc cố gắng gọi các Tool (như cố lấy ID khách sạn dù user chỉ nói "Hello") dẫn đến tốn thời gian (latency cao) và phản hồi mất tự nhiên, trong khi Chatbot thường trả lời mượt mà ngay lập tức.
3.  **Observation**: Phản hồi từ môi trường (Observation) đóng vai trò như một "lưới an toàn". Ví dụ, khi hàm `get_hotel_details` trả về list các tiện ích: `Available: Swimming Pool, Fitness Center | Not available: Pet Friendly`, Observation này ngay lập tức định hướng cho Agent chặn user nếu user muốn mang theo thú cưng, điều mà LLM không thể tự biết nếu chỉ dựa vào trọng số mô hình.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Thay vì dùng mock dictionary `HOTEL_DETAILS` lưu trên RAM, tôi sẽ kết nối công cụ này với một RESTful API hoặc Database thực tế (như PostgreSQL) thông qua ORM. Sử dụng `asyncio` để các Tool calls (đặc biệt là khi gọi qua mạng) không chặn luồng chính của hệ thống.
- **Safety**: Cần thêm bước kiểm tra (Sanitize) đầu vào của `hotel_id` nghiêm ngặt hơn để chống lại các lỗ hổng như Prompt Injection hoặc SQL Injection khi kết nối DB thật. Có thể dùng Pydantic models để validate data types thay vì ép kiểu thủ công bằng `str()` hay `int()`.
- **Performance**: Khi số lượng công cụ tăng lên, không thể nhồi nhét tất cả tool descriptions vào system prompt vì sẽ vượt quá context window. Cần triển khai hệ thống Vector DB để lưu trữ metadata của các tools, sau đó dùng RAG (Retrieval-Augmented Generation) để lấy ra đúng công cụ cần thiết (ví dụ: chỉ load `get_hotel_details` khi user nhắc đến du lịch/lưu trú).
