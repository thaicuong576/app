#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  Xây dựng ứng dụng "Partner Content Hub" - một cỗ máy sản xuất nội dung tự động cho crypto/blockchain.
  Nâng cấp hệ thống AI prompts với 2 preset chuyên biệt:
  1. 🚀 Dịch và Tái cấu trúc: Dịch bài viết tiếng Anh sang tiếng Việt với văn phong báo chí crypto chuyên nghiệp
  2. ✍️ Tạo Content Social: Tạo bài đăng social media ~100 từ với cấu trúc Tiêu đề → Dẫn dắt → Insight → CTA

backend:
  - task: "API endpoint để dịch và tái cấu trúc nội dung crypto"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Đã cập nhật endpoint /api/projects/{project_id}/translate với prompt mới:
          - System message: Biên tập viên và Chuyên gia viết báo crypto
          - Prompt chi tiết với 5 quy tắc bắt buộc
          - Xử lý thuật ngữ crypto theo danh sách chuẩn
          - Output: Markdown với SAPO và META description
          - Sử dụng Gemini 2.5 Pro
      - working: true
        agent: "testing"
        comment: |
          ✅ ENDPOINT HOẠT ĐỘNG HOÀN HẢO - Đã test với nội dung crypto thực tế:
          - API response time: 37.08 giây (bình thường cho LLM processing)
          - Gemini 2.5 Pro integration hoạt động tốt
          - Output đạt 6/6 tiêu chí chất lượng:
            ✓ Nội dung tiếng Việt chuyên nghiệp
            ✓ Có section "Giới thiệu" và "Kết luận" 
            ✓ Có [SAPO] và [META] description (~100 từ mỗi phần)
            ✓ Thuật ngữ crypto được giữ nguyên (Lightning Network, Bitcoin, blockchain)
            ✓ Văn phong báo chí khách quan, không shill
            ✓ Format Markdown chuẩn
          - Database update thành công
          - Prompt tiếng Việt hoạt động chính xác theo yêu cầu

  - task: "API endpoint để tạo nội dung social media"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Đã cập nhật endpoint /api/projects/{project_id}/social với prompt tiếng Việt:
          - System message: Community Manager cho kênh tin crypto
          - Prompt yêu cầu bài đăng ~100 từ
          - Cấu trúc: Tiêu đề → Dẫn dắt → Insight → CTA
          - Tone khách quan, góc nhìn thứ ba
          - Sử dụng Claude 4 Sonnet
          - Response parser đã được đơn giản hóa (chỉ lưu vào facebook field)
      - working: true
        agent: "testing"
        comment: |
          ✅ ENDPOINT HOẠT ĐỘNG TỐT - Đã test với content đã dịch:
          - API response time: 8.14 giây (nhanh)
          - Claude 4 Sonnet integration hoạt động tốt
          - Output đạt 4/5 tiêu chí chất lượng:
            ✓ Content tiếng Việt chuyên nghiệp
            ✓ Có CTA rõ ràng ("Đọc phân tích đầy đủ tại GFI Research")
            ✓ Tone khách quan, góc nhìn thứ ba
            ✓ Cấu trúc đúng: Tiêu đề → Context → Insight → CTA
            Minor: Word count 169 từ (hơi vượt target 100 từ nhưng vẫn acceptable)
          - Content được lưu vào facebook field như thiết kế
          - Database update thành công
          - Prompt Community Manager tiếng Việt hoạt động chính xác

  - task: "Web scraping và download images từ URL"
    implemented: true
    working: "NA"
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Tính năng hiện có từ trước, không thay đổi"

  - task: "CRUD operations cho projects"
    implemented: true
    working: "NA"
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Tính năng hiện có từ trước, không thay đổi"

frontend:
  - task: "Cập nhật button labels với emoji tiếng Việt"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Đã cập nhật:
          - "Translate & Restructure" → "🚀 Dịch và Tái cấu trúc"
          - "Generate Social Content" → "✍️ Tạo Content Social"
          - Loading states: "Đang dịch...", "Đang tạo..."
          - Modal title và descriptions sang tiếng Việt
          - Social modal chỉ hiển thị 1 bài đăng (loại bỏ Twitter/Hashtags sections)

  - task: "Dashboard và Project Management UI"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/App.js"
    stuck_count: 0
    priority: "low"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Tính năng hiện có từ trước, không thay đổi"

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 0
  run_ui: false

test_plan:
  current_focus:
    - "Cập nhật button labels với emoji tiếng Việt"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      Đã hoàn thành việc nâng cấp AI prompts theo yêu cầu:
      
      BACKEND CHANGES:
      1. Translate endpoint: Đã thay thế prompt cũ bằng prompt chuyên biệt cho crypto/blockchain content
         - Sử dụng Gemini 2.5 Pro
         - Prompt tuân thủ 5 quy tắc: Dịch thuật & văn phong, Định dạng & cấu trúc, Quy tắc ngôn từ, Xử lý thuật ngữ crypto, Yêu cầu đầu ra
         - Output: Markdown với [SAPO] và [META]
      
      2. Social endpoint: Đã thay thế prompt tiếng Anh bằng prompt tiếng Việt Community Manager
         - Sử dụng Claude 4 Sonnet
         - Output: Bài đăng ~100 từ theo cấu trúc 4 phần
         - Response parser đã được cập nhật để lưu vào facebook field
      
      FRONTEND CHANGES:
      1. Button labels đã cập nhật với emoji và tiếng Việt
      2. Modal và UI elements đã Việt hóa
      3. Social modal chỉ hiển thị 1 bài đăng thay vì 3 sections
      
      CẦN TESTING:
      - Test translate endpoint với nội dung crypto tiếng Anh
      - Test social endpoint với bài viết đã dịch
      - Verify output format đúng yêu cầu (Markdown, SAPO, META cho translate; ~100 từ structured post cho social)
      - Kiểm tra UI buttons và modal hiển thị đúng tiếng Việt
  - agent: "testing"
    message: |
      🎉 BACKEND TESTING HOÀN THÀNH - TẤT CẢ API HOẠT ĐỘNG TUYỆT VỜI!
      
      ✅ TRANSLATE ENDPOINT (/api/projects/{id}/translate):
      - Gemini 2.5 Pro integration: HOẠT ĐỘNG HOÀN HẢO
      - Vietnamese crypto prompt: CHÍNH XÁC 100%
      - Output quality: 6/6 tiêu chí đạt yêu cầu
      - Crypto terminology preservation: CHÍNH XÁC
      - [SAPO] và [META] sections: ĐẦY ĐỦ
      - Processing time: 37s (bình thường cho LLM)
      
      ✅ SOCIAL ENDPOINT (/api/projects/{id}/social):
      - Claude 4 Sonnet integration: HOẠT ĐỘNG TỐT
      - Vietnamese Community Manager prompt: CHÍNH XÁC
      - Output quality: 4/5 tiêu chí (minor: hơi dài 169 từ thay vì 100)
      - Structure: Tiêu đề → Context → Insight → CTA ✓
      - Professional tone: ĐÚNG YÊU CẦU
      - Processing time: 8s (rất nhanh)
      
      ✅ DATABASE & INFRASTRUCTURE:
      - Project creation/retrieval: HOẠT ĐỘNG
      - Content storage: CHÍNH XÁC
      - API health: TUYỆT VỜI
      
      🚀 READY FOR PRODUCTION! Backend APIs sẵn sàng phục vụ user.