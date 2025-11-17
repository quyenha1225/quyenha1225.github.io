USE ThuVienDB;
GO
PRINT N'--- Bắt đầu thêm dữ liệu mẫu ---';

-- 1. Thêm 498 nhân viên ngẫu nhiên 
PRINT N'Thêm 498 dòng vào [employees]...';
DECLARE @i_emp INT = 1;
DECLARE @day1 INT, @day2 INT;
DECLARE @schedule VARCHAR(30);

BEGIN TRAN EmpTran
WHILE @i_emp <= 498
BEGIN
    SET @day1 = CAST(RAND() * 30 AS INT) + 1;
    SET @day2 = CAST(RAND() * 30 AS INT) + 1;
    IF @day1 = @day2 SET @day2 = (@day1 % 30) + 1;
    SET @schedule = CAST(@day1 AS VARCHAR(2)) + ',' + CAST(@day2 AS VARCHAR(2));

    INSERT INTO employees (name, position, username, password, is_admin, work_date, schedule_days)
    VALUES (
        N'Nhân viên ' + CAST(@i_emp + 2 AS NVARCHAR(10)), -- Bắt đầu từ 'Nhân viên 3'
        CASE (@i_emp % 3) WHEN 0 THEN N'Thủ thư' WHEN 1 THEN N'Bảo vệ' ELSE N'Nhân viên kho' END,
        'user' + CAST(@i_emp + 2 AS NVARCHAR(10)), -- Bắt đầu từ 'user3'
        'pass' + CAST(@i_emp + 2 AS NVARCHAR(10)),
        0,
        DATEADD(day, -CAST(RAND() * 1000 AS INT), GETDATE()),
        @schedule
    );
    SET @i_emp = @i_emp + 1;
END
COMMIT TRAN EmpTran
PRINT N'-> Hoàn tất [employees] (Tổng cộng 500).';
GO

-- 2. Thêm 500 người mượn
PRINT N'Thêm 500 dòng vào [borrowers]...';
DECLARE @i_bor INT = 1;
BEGIN TRAN BorTran
WHILE @i_bor <= 500
BEGIN
    INSERT INTO borrowers (name, phone, email)
    VALUES (
        N'Người mượn ' + CAST(@i_bor AS NVARCHAR(10)),
        N'09' + RIGHT('00000000' + CAST(CAST(RAND() * 100000000 AS INT) AS NVARCHAR(8)), 8),
        N'nguoimuon' + CAST(@i_bor AS NVARCHAR(10)) + N'@testmail.com'
    );
    SET @i_bor = @i_bor + 1;
END
COMMIT TRAN BorTran
PRINT N'-> Hoàn tất [borrowers].';
GO
-- 3. Thêm 500 sách
PRINT N'Thêm 500 dòng vào [books]...';
DECLARE @i_book INT = 1;
BEGIN TRAN BookTran
WHILE @i_book <= 500
BEGIN
    INSERT INTO books (title, author, published_year, category, status)
    VALUES (
        N'Tên sách ' + CAST(@i_book AS NVARCHAR(10)),
        N'Tác giả ' + CAST(@i_book AS NVARCHAR(10)),
        1980 + CAST(RAND() * 45 AS INT),
        CASE (@i_book % 5)
            WHEN 0 THEN N'Tiểu thuyết'
            WHEN 1 THEN N'Khoa học'
            WHEN 2 THEN N'Lịch sử'
            WHEN 3 THEN N'Kỹ năng sống'
            ELSE N'Trinh thám'
        END,
        N'Có sẵn'
    );
    SET @i_book = @i_book + 1;
END
COMMIT TRAN BookTran
PRINT N'-> Hoàn tất [books].';
GO

-- 4. Thêm 500 phiếu mượn
-- (Giả định ID của 500 employees là 1-500, borrowers là 1-500, books là 1-500)
PRINT N'Thêm 500 dòng vào [loans]...';
DECLARE @i_loan INT = 1;
DECLARE @borrow_date DATE, @is_returned BIT, @return_date DATE;

-- Lấy ID cuối cùng của mỗi bảng để tham chiếu
-- (An toàn hơn là giả định 1-500, phòng trường hợp bạn đã có dữ liệu)
DECLARE @max_emp_id INT = (SELECT MAX(employee_id) FROM employees);
DECLARE @min_emp_id INT = (SELECT MIN(employee_id) FROM employees);
DECLARE @max_bor_id INT = (SELECT MAX(borrower_id) FROM borrowers);
DECLARE @min_bor_id INT = (SELECT MIN(borrower_id) FROM borrowers);
DECLARE @max_book_id INT = (SELECT MAX(book_id) FROM books);
DECLARE @min_book_id INT = (SELECT MIN(book_id) FROM books);

BEGIN TRAN LoanTran
WHILE @i_loan <= 500
BEGIN
    SET @borrow_date = DATEADD(day, -CAST(RAND() * 180 AS INT), GETDATE());
    SET @is_returned = CASE WHEN RAND() > 0.3 THEN 1 ELSE 0 END;
    
    IF @is_returned = 1
        SET @return_date = DATEADD(day, CAST(RAND() * 30 AS INT) + 1, @borrow_date);
    ELSE
        SET @return_date = NULL;

    INSERT INTO loans (borrower_id, book_id, employee_id, borrow_date, return_date, is_returned)
    VALUES (
        -- ID ngẫu nhiên trong khoảng min-max của bảng
        CAST(RAND() * (@max_bor_id - @min_bor_id) + @min_bor_id AS INT),
        -- Lấy 500 ID sách cuối cùng
        (@max_book_id - 500) + @i_loan,
        CAST(RAND() * (@max_emp_id - @min_emp_id) + @min_emp_id AS INT),
        @borrow_date,
        @return_date,
        @is_returned
    );
    SET @i_loan = @i_loan + 1;
END
COMMIT TRAN LoanTran
PRINT N'-> Hoàn tất [loans].';
GO

-- 5. Cập nhật trạng thái sách (cho những sách vừa mượn)
PRINT N'Cập nhật trạng thái sách đã bị mượn (chưa trả)...';
UPDATE B
SET B.status = N'Đã mượn'
FROM books AS B
JOIN loans AS L ON B.book_id = L.book_id
WHERE L.is_returned = 0;
go
