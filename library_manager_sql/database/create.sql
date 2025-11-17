-- 1. TẠO DATABASE
IF DB_ID('ThuVienDB') IS NULL
BEGIN
    CREATE DATABASE ThuVienDB;
END
GO
USE ThuVienDB;
GO

-- 2. XÓA BẢNG (NẾU TỒN TẠI)
IF OBJECT_ID('loans', 'U') IS NOT NULL DROP TABLE loans;
IF OBJECT_ID('loan_receipts', 'U') IS NOT NULL DROP TABLE loan_receipts;
IF OBJECT_ID('borrowers', 'U') IS NOT NULL DROP TABLE borrowers;
IF OBJECT_ID('books', 'U') IS NOT NULL DROP TABLE books;
IF OBJECT_ID('employees', 'U') IS NOT NULL DROP TABLE employees;
GO

-- 3. TẠO BẢNG employees
CREATE TABLE employees (
    employee_id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(200) NOT NULL,
    position NVARCHAR(100),
    username NVARCHAR(100) UNIQUE,
    password NVARCHAR(200),
    is_admin BIT DEFAULT 0,
    work_date DATE NULL,
    schedule_days NVARCHAR(100)
);
GO

-- 4. TẠO BẢNG books
CREATE TABLE books (
    book_id INT IDENTITY(1,1) PRIMARY KEY,
    title NVARCHAR(300) NOT NULL,
    author NVARCHAR(200),
    published_year INT,
    category NVARCHAR(100),
    status NVARCHAR(50) DEFAULT N'Có sẵn'
);
GO

-- 5. TẠO BẢNG borrowers
CREATE TABLE borrowers (
    borrower_id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(200) NOT NULL,
    phone NVARCHAR(50),
    email NVARCHAR(200)
);
ALTER TABLE borrowers ADD CONSTRAINT UQ_Borrower_Phone UNIQUE(phone);
ALTER TABLE borrowers ADD CONSTRAINT UQ_Borrower_Email UNIQUE(email);
GO

-- 6. TẠO BẢNG loan_receipts (phiếu mượn)
CREATE TABLE loan_receipts (
    receipt_id INT IDENTITY(1,1) PRIMARY KEY,
    borrower_id INT NOT NULL,
    borrow_date DATE,
    due_date DATE,
    return_date DATE,
    employee_id INT,
    note NVARCHAR(MAX),
    FOREIGN KEY (borrower_id) REFERENCES borrowers(borrower_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);
GO
-- 7. TẠO BẢNG loans (chi tiết sách mượn trong phiếu)
CREATE TABLE loans (
    loan_id INT IDENTITY(1,1) PRIMARY KEY,
    receipt_id INT NOT NULL,
    book_id INT NOT NULL,                    -- PHẢI CÓ
    borrow_date DATE,
    return_date DATE,
    is_returned BIT DEFAULT 0,
    FOREIGN KEY (receipt_id) REFERENCES loan_receipts(receipt_id),
    FOREIGN KEY (book_id) REFERENCES books(book_id)  -- PHẢI CÓ
);


-- 8. THÊM DỮ LIỆU MẪU--
INSERT INTO employees (name, position, username, password, is_admin, work_date, schedule_days)
VALUES
(N'Admin Thư Viện', N'Quản trị viên', 'admin', 'admin123', 1, GETDATE(), N'T2-T7'),
(N'Nhân viên 1', N'Thủ thư', 'staff', 'staff123', 0, GETDATE(), N'T3-T6');
GO

INSERT INTO books (title, author, published_year, category)
VALUES
(N'Lập trình C#', N'Nguyễn Văn A', 2020, N'Tin học'),
(N'Toán rời rạc', N'Trần Thị B', 2018, N'Toán học'),
(N'Văn học Việt Nam', N'Nguyễn Du', 1802, N'Văn học');
GO

INSERT INTO borrowers (name, phone, email)
VALUES
(N'Nguyễn Văn Nam', '0901234567', 'nam@gmail.com'),
(N'Trần Thị Lan', '0912345678', 'lan@yahoo.com');
GO


-- 9. TRIGGERS
-- Khi thêm chi tiết mượn (loans)
CREATE TRIGGER trg_HandleBorrow ON loans AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    -- Cập nhật trạng thái sách
    UPDATE books
    SET status = N'Đã mượn'
    WHERE book_id IN (SELECT book_id FROM inserted WHERE is_returned = 0);

    -- Cập nhật ngày mượn (nếu chưa có)
    UPDATE loans
    SET borrow_date = COALESCE(borrow_date, GETDATE())
    WHERE loan_id IN (SELECT loan_id FROM inserted);

    -- Cập nhật ngày làm việc nhân viên (từ phiếu)
    UPDATE e
    SET work_date = GETDATE()
    FROM employees e
    INNER JOIN loan_receipts r ON e.employee_id = r.employee_id
    INNER JOIN inserted i ON r.receipt_id = i.receipt_id;
END;
GO

-- Khi trả sách (cập nhật is_returned = 1)
CREATE TRIGGER trg_HandleReturn ON loans AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF UPDATE(is_returned)
    BEGIN
        -- Cập nhật trạng thái sách khi trả
        UPDATE books
        SET status = N'Có sẵn'
        FROM books b
        INNER JOIN inserted i ON b.book_id = i.book_id
        INNER JOIN deleted d ON i.loan_id = d.loan_id
        WHERE i.is_returned = 1 AND d.is_returned = 0;

        -- Cập nhật ngày trả
        UPDATE loans
        SET return_date = GETDATE()
        FROM inserted i
        INNER JOIN deleted d ON i.loan_id = d.loan_id
        WHERE i.is_returned = 1 AND d.is_returned = 0;
    END
END;
GO

-- Khi xóa mượn (nếu chưa trả)
CREATE TRIGGER trg_HandleDeleteLoan ON loans AFTER DELETE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE books
    SET status = N'Có sẵn'
    WHERE book_id IN (SELECT book_id FROM deleted WHERE is_returned = 0);
END;
GO


-- 10. INDEXES--------------
CREATE INDEX IX_Loans_ReceiptID ON loans(receipt_id);
CREATE INDEX IX_Loans_BookID ON loans(book_id);
CREATE INDEX IX_LoanReceipts_BorrowerID ON loan_receipts(borrower_id);
CREATE INDEX IX_LoanReceipts_EmployeeID ON loan_receipts(employee_id);
CREATE INDEX IX_Books_Title ON books(title);
CREATE INDEX IX_Borrowers_Name ON borrowers(name);
CREATE INDEX IX_Borrowers_Phone ON borrowers(phone);
GO

------------------------------------------------------------
-- 11. VIEWS
------------------------------------------------------------
IF OBJECT_ID('vw_ThongTinDocGia', 'V') IS NOT NULL DROP VIEW vw_ThongTinDocGia;
IF OBJECT_ID('vw_ThongTinSach', 'V') IS NOT NULL DROP VIEW vw_ThongTinSach;
IF OBJECT_ID('vw_ChiTietMuonTra', 'V') IS NOT NULL DROP VIEW vw_ChiTietMuonTra;
GO

CREATE VIEW vw_ThongTinDocGia AS
SELECT borrower_id, name, phone, email FROM borrowers;
GO

CREATE VIEW vw_ThongTinSach AS
SELECT book_id, title, author, published_year, category, status FROM books;
GO

CREATE VIEW vw_ChiTietMuonTra AS
SELECT
    l.loan_id AS MaChiTiet,
    r.receipt_id AS MaPhieu,
    b.name AS TenDocGia,
    b.phone AS SoDienThoai,
    bk.title AS TenSach,
    bk.author AS TacGia,
    e.name AS TenNhanVien,
    COALESCE(l.borrow_date, r.borrow_date) AS NgayMuon,
    l.return_date AS NgayTra,
    CASE WHEN l.is_returned = 1 THEN N'Đã trả' ELSE N'Đang mượn' END AS TrangThai
FROM loans l
INNER JOIN loan_receipts r ON l.receipt_id = r.receipt_id
LEFT JOIN borrowers b ON r.borrower_id = b.borrower_id
LEFT JOIN books bk ON l.book_id = bk.book_id
LEFT JOIN employees e ON r.employee_id = e.employee_id;
GO