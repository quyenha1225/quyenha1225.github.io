// Tạo collection "employees"
db.createCollection("employees");

// Thêm dữ liệu mẫu vào collection "employees"
db.employees.insertMany([
  {
    "employee_id": 1,
    "name": "Admin Thư Viện",
    "position": "Quản trị viên",
    "username": "admin",
    "password": "admin123",
    "is_admin": true,
    "work_date": new Date()  // Ngày làm việc
  },
  {
    "employee_id": 2,
    "name": "Nhân viên 1",
    "position": "Thủ thư",
    "username": "staff",
    "password": "staff123",
    "is_admin": false,
    "work_date": new Date()
  }
]);

// Tạo collection "books"
db.createCollection("books");

// Thêm dữ liệu vào collection "books"
db.books.insertMany([
  {
    "book_id": 1,
    "title": "Sách A",
    "author": "Tác giả A",
    "published_year": 2022,
    "category": "Lịch sử",
    "status": "Có sẵn"
  },
  {
    "book_id": 2,
    "title": "Sách B",
    "author": "Tác giả B",
    "published_year": 2021,
    "category": "Khoa học",
    "status": "Có sẵn"
  }
]);

// Tạo collection "borrowers"
db.createCollection("borrowers");

// Thêm dữ liệu vào collection "borrowers"
db.borrowers.insertMany([
  {
    "borrower_id": 1,
    "name": "Nguyễn Văn A",
    "phone": "0123456789",
    "email": "nguyenvana@example.com"
  },
  {
    "borrower_id": 2,
    "name": "Trần Thị B",
    "phone": "0987654321",
    "email": "tranb@example.com"
  }
]);

// Tạo collection "loans"
db.createCollection("loans");

// Thêm dữ liệu vào collection "loans"
db.loans.insertMany([
  {
    "loan_id": 1,
    "borrower_id": 1,
    "book_id": 1,
    "employee_id": 1,
    "borrow_date": new Date("2022-01-01"),
    "return_date": new Date("2022-01-15"),
    "is_returned": false
  },
  {
    "loan_id": 2,
    "borrower_id": 2,
    "book_id": 2,
    "employee_id": 2,
    "borrow_date": new Date("2022-02-01"),
    "return_date": new Date("2022-02-15"),
    "is_returned": true
  }
]);

// Giả sử bạn đã thêm một loan mới vào collection "loans"
db.books.updateOne(
  { "book_id": 1 },
  { $set: { "status": "Đã mượn" } }
);

// Cập nhật ngày mượn vào "loans"
db.loans.updateOne(
  { "loan_id": 1 },
  { $set: { "borrow_date": new Date() } }
);

// Cập nhật ngày làm việc của nhân viên
db.employees.updateOne(
  { "employee_id": 1 },
  { $set: { "work_date": new Date() } }
);

// Cập nhật trạng thái sách về "Có sẵn"
db.books.updateOne(
  { "book_id": 1 },
  { $set: { "status": "Có sẵn" } }
);

// Cập nhật ngày trả sách trong "loans"
db.loans.updateOne(
  { "loan_id": 1 },
  { $set: { "return_date": new Date(), "is_returned": true } }
);

// Cập nhật ngày làm việc của nhân viên
db.employees.updateOne(
  { "employee_id": 1 },
  { $set: { "work_date": new Date() } }
);

db.borrowers.aggregate([
  {
    $project: {
      "borrower_id": 1,
      "name": 1,
      "phone": 1,
      "email": 1
    }
  }
]);

db.books.aggregate([
  {
    $project: {
      "book_id": 1,
      "title": 1,
      "author": 1,
      "published_year": 1,
      "category": 1,
      "status": 1
    }
  }
]);

db.loans.aggregate([
  {
    $lookup: {
      from: "borrowers",
      localField: "borrower_id",
      foreignField: "borrower_id",
      as: "borrower_info"
    }
  },
  {
    $lookup: {
      from: "books",
      localField: "book_id",
      foreignField: "book_id",
      as: "book_info"
    }
  },
  {
    $lookup: {
      from: "employees",
      localField: "employee_id",
      foreignField: "employee_id",
      as: "employee_info"
    }
  },
  {
    $project: {
      "loan_id": 1,
      "borrower_name": { $arrayElemAt: ["$borrower_info.name", 0] },
      "book_title": { $arrayElemAt: ["$book_info.title", 0] },
      "employee_name": { $arrayElemAt: ["$employee_info.name", 0] },
      "borrow_date": 1,
      "return_date": 1,
      "status": { $cond: [{ $eq: ["$is_returned", true] }, "Đã trả", "Đang mượn"] }
    }
  }
]);

db.employees.updateMany({}, { $set: { schedule_days: "" } });

db.counters.insertOne({ _id: "employees", last_id: 2 });