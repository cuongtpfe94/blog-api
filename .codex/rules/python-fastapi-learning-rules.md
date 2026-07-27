# Quy Tắc Làm Việc Và Coding Cho Dự Án Blog API

Các quy tắc này áp dụng cho quá trình học và xây dựng dự án **FastAPI Blog API**. Mục tiêu là giúp người học tự gõ code, hiểu rõ kiến trúc, và hình thành thói quen viết code backend sạch, dễ bảo trì.

## 1. Chính sách chỉnh sửa file

Codex **không được phép tự ý sửa, tạo hoặc xóa bất kỳ file nào** trong dự án.

### Luôn luôn

- Phân tích code hiện có trước khi trả lời.
- Giải thích vấn đề hoặc mục tiêu cần làm.
- Trả về code hoàn chỉnh bằng Markdown.
- Ghi rõ file nào cần đặt code.
- Hiển thị unified diff nếu cần so sánh thay đổi.
- Để người dùng tự copy hoặc tự gõ code vào project.

### Không bao giờ

- Không tự sửa file.
- Không tự tạo file.
- Không tự xóa file.
- Không chạy command có tác dụng ghi file.
- Không chạy formatter/codegen/migration nếu chúng làm thay đổi file.
- Không apply patch.
- Không thay đổi repo nếu người dùng chưa yêu cầu rõ ràng.

## 2. Định dạng trả lời code

Khi trả lời code, luôn dùng Markdown theo mẫu:

````markdown
## File: app/example.py

```python
# code ở đây
```
````

````

Nếu cần nhiều file, trình bày từng file riêng biệt:

```markdown
## File: app/controllers/example.py

```python
# controller code
````

## File: app/services/example.py

```python
# service code
```

````

## 3. Kiến trúc 3 lớp rõ ràng

Dự án sử dụng kiến trúc phân lớp:

- **Controller**: nhận request, validate input, gọi service, trả response.
- **Service**: chứa business logic, điều phối repository, không truy vấn database trực tiếp.
- **Repository**: chứa toàn bộ thao tác truy vấn database như CRUD, filter, join, pagination.

### Sai

```python
@router.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
````

### Đúng

```python
@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.get_user_by_id(user_id)
```

## 4. Không truy vấn database trong service

Service không được dùng trực tiếp:

- `select(...)`
- `insert(...)`
- `update(...)`
- `delete(...)`
- `db.execute(...)`
- `db.commit(...)`
- `db.refresh(...)`

Toàn bộ logic truy vấn database phải nằm trong repository.

## 5. Không truy vấn database trong vòng lặp

Không gọi database trong `for` hoặc `while`.

### Sai

```python
for post in posts:
    comments = await comment_repository.list_by_post_id(post.id)
```

### Đúng

```python
post_ids = [post.id for post in posts]
comments_by_post_id = await comment_repository.list_grouped_by_post_ids(post_ids)
```

## 6. Controller không chứa business logic

Controller chỉ nên làm các việc sau:

- Nhận path/query/body parameter.
- Inject dependency bằng `Depends`.
- Gọi service.
- Trả response.
- Khai báo `response_model`, `status_code`, `tags`.

Controller không xử lý:

- Hash password.
- Kiểm tra quyền phức tạp.
- Tạo slug.
- Tính toán nghiệp vụ.
- Truy vấn database.

## 7. Bắt buộc dùng schema cho input/output

Mọi request body và response nên có Pydantic schema rõ ràng.

Ví dụ:

```python
from pydantic import BaseModel, EmailStr


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    display_name: str
    is_active: bool
```

Không trả trực tiếp dữ liệu nhạy cảm như:

- `hashed_password`
- refresh token đã lưu trong database
- secret key
- internal config

## 8. Bắt buộc khai báo type hint

Mọi hàm phải khai báo type cho tham số và giá trị trả về.

### Sai

```python
def get_user(user_id):
    return user_repository.get_by_id(user_id)
```

### Đúng

```python
async def get_user(user_id: int) -> User | None:
    return await user_repository.get_by_id(user_id)
```

## 9. Hàm phải ngắn và có một trách nhiệm

Mỗi hàm chỉ nên làm một việc rõ ràng.

Ưu tiên:

- Hàm dài khoảng 20-30 dòng trở xuống.
- Không truyền quá nhiều tham số.
- Tách logic phức tạp thành hàm nhỏ.
- Không gom nhiều nghiệp vụ vào một hàm.

## 10. Hạn chế lồng logic quá sâu

Không nên lồng quá:

- 2 tầng `if`
- 2 tầng vòng lặp
- nhiều nhánh điều kiện phức tạp trong cùng một hàm

Ưu tiên dùng guard clause:

```python
if user is None:
    raise NotFoundError("User not found")

if not user.is_active:
    raise ForbiddenError("User is inactive")
```

## 11. Service cần docstring và logging

Các hàm nghiệp vụ chính trong service nên có docstring và logging.

```python
async def publish_post(self, post_id: int, current_user: User) -> Post:
    """
    Publish a draft post.

    Args:
        post_id: ID của bài viết cần publish.
        current_user: User đang thực hiện thao tác.

    Returns:
        Bài viết sau khi được publish.
    """
    logger.info("Publishing post_id=%s by user_id=%s", post_id, current_user.id)
    post = await self.post_repository.get_by_id(post_id)

    if post is None:
        logger.warning("Post not found: post_id=%s", post_id)
        raise NotFoundError("Post not found")

    return await self.post_repository.publish(post)
```

## 12. Quy chuẩn đặt tên

| Loại        | Quy tắc                     |
| ----------- | --------------------------- |
| Class       | PascalCase                  |
| Hàm         | snake_case                  |
| Biến        | snake_case                  |
| Hằng số     | UPPER_CASE                  |
| Module/file | snake_case                  |
| API path    | kebab-case hoặc plural noun |

Ví dụ:

```python
class PostService:
    pass


async def get_post_by_slug(slug: str) -> Post | None:
    pass


MAX_PAGE_SIZE = 100
```

## 13. Quy tắc path variable và query parameter

Dùng path variable cho định danh tài nguyên cụ thể.

```text
GET /posts/{post_id}
GET /users/{user_id}
GET /categories/{category_id}
```

Dùng query parameter cho filter, search, sort, pagination.

```text
GET /posts?category=fastapi&limit=20&offset=0
GET /posts?search=postgres
```

## 14. Quy tắc cho FastAPI dependency

Dependency nên dùng cho:

- Database session.
- Current user.
- Current admin user.
- Service injection.
- Repository injection nếu cần.
- Security/authentication.

Không lạm dụng dependency cho logic nghiệp vụ chính.

## 15. Quy tắc cho database với SQLAlchemy async

Dự án dùng PostgreSQL với SQLAlchemy async.

Ưu tiên:

- `AsyncSession`
- `select`
- repository riêng cho từng aggregate/entity
- transaction rõ ràng
- tránh lazy loading gây lỗi async hoặc N+1 query

Repository chịu trách nhiệm:

- Query database.
- Commit/flush/refresh nếu convention của dự án yêu cầu.
- Mapping điều kiện filter.
- Pagination query.

## 16. Quy tắc migration

Không dùng `Base.metadata.create_all()` cho workflow chính của dự án.

Thay vào đó dùng Alembic:

- Tạo migration khi thay đổi model.
- Review migration trước khi chạy.
- Không chỉnh sửa database schema thủ công nếu schema thuộc project.

## 17. Quy tắc bảo mật

Không bao giờ:

- Log password.
- Trả `hashed_password` trong response.
- Hard-code secret key trong source code.
- Lưu JWT secret trong code.
- Bỏ qua kiểm tra quyền ở endpoint ghi dữ liệu.

Auth mặc định:

- JWT access token.
- JWT refresh token.
- Password hashing.
- Dependency `get_current_user`.
- Dependency `get_current_admin_user`.

## 18. Quy tắc lỗi và response

Nên chuẩn hóa lỗi bằng custom exception và exception handler.

Lỗi nên có:

- HTTP status code đúng.
- Message rõ ràng.
- Error code nếu cần.
- Không expose stack trace cho client.

Ví dụ lỗi nghiệp vụ:

```python
raise NotFoundError("Post not found")
raise ConflictError("Email already exists")
raise ForbiddenError("Admin permission required")
```

## 19. Quy tắc testing

Mỗi nghiệp vụ chính nên có test:

- Health check.
- User CRUD.
- Login/refresh token.
- Permission.
- Category CRUD.
- Post CRUD.
- Public post listing.
- Comment moderation.

Test nên kiểm tra:

- Success case.
- Validation error.
- Not found.
- Permission denied.
- Conflict/duplicate data.

## 20. Nguyên tắc học khi làm việc với Codex

Khi bắt đầu một nghiệp vụ mới, luôn đi theo thứ tự:

1. Hiểu mục tiêu nghiệp vụ.
2. Thiết kế database model.
3. Thiết kế Pydantic schema.
4. Viết repository.
5. Viết service.
6. Viết controller/router.
7. Test bằng Swagger hoặc pytest.
8. Refactor nếu có lý do rõ ràng.

Codex chỉ đóng vai trò:

- Giải thích.
- Gợi ý thiết kế.
- Trả code mẫu.
- Review code.
- Chỉ ra lỗi.
- Đưa diff để người dùng tự sửa.

Người dùng là người trực tiếp viết code để học và ghi nhớ lâu hơn.
