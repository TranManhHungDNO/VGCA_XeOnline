<div align="center">

<img src="docs/images/logo.png" width="180">

# VGCA XeOnline

### Linux Digital Signature Platform

**PKCS#11 • Native Messaging • Chrome Extension • Open Source • Digital Transformation**

---

*Nền tảng ký số dành cho hệ điều hành Linux và các OS nền tảng mã nguồn mở*

</div>

---

# 📖 Giới thiệu

VGCA XeOnline là nền tảng ký số được phát triển dành riêng cho các hệ điều hành Linux và các nền tảng mã nguồn mở, hỗ trợ sử dụng USB Token thông qua chuẩn **PKCS#11**.

Dự án hướng tới việc xây dựng một nền tảng ký số thống nhất, giúp các ứng dụng Desktop, Web Browser và các hệ thống nghiệp vụ có thể sử dụng chung một cơ chế ký số an toàn, hiện đại và dễ tích hợp.

Không chỉ là một ứng dụng ký PDF, VGCA XeOnline được định hướng trở thành nền tảng trung gian (Digital Signature Platform) phục vụ cho các hệ thống quản lý văn bản điện tử, Cổng Dịch vụ công, Một cửa điện tử, Hệ thống điều hành tác nghiệp và các ứng dụng Web sử dụng chữ ký số.

---

# 🎯 Sứ mệnh

VGCA XeOnline được phát triển với mong muốn mở rộng khả năng sử dụng chữ ký số USB Token từ môi trường Windows sang các hệ điều hành mã nguồn mở như Linux Mint, Ubuntu, Debian và các bản phân phối Linux khác.

Thông qua việc hỗ trợ chuẩn PKCS#11, Native Messaging và Chrome Extension, dự án góp phần xây dựng một môi trường làm việc số hiện đại trên nền tảng Linux, giúp các cơ quan, tổ chức, doanh nghiệp và người dùng có thêm lựa chọn triển khai các giải pháp ký số trên hệ điều hành mã nguồn mở được cấp phép hợp pháp.

---

# 🌍 Tầm nhìn

VGCA XeOnline hướng tới trở thành nền tảng ký số dành cho Linux có khả năng tương thích rộng rãi với các USB Token phổ biến tại Việt Nam, đồng thời cung cấp một kiến trúc mở để các ứng dụng Desktop và Web có thể dễ dàng tích hợp.

Trong tương lai, dự án sẽ phát triển thành một hệ sinh thái ký số hoàn chỉnh bao gồm Desktop Application, Native Messaging Host, Chrome Extension, Driver Manager, Certificate Manager, PKCS#11 Engine và các API mở phục vụ chuyển đổi số.

---

# 🇻🇳 Định hướng phát triển

VGCA XeOnline được xây dựng với định hướng góp phần thúc đẩy việc ứng dụng các hệ điều hành mã nguồn mở trong hoạt động của cơ quan nhà nước, doanh nghiệp và tổ chức.

Dự án mong muốn tạo thêm lựa chọn triển khai trên các hệ điều hành nguồn mở có giấy phép hợp pháp, góp phần giảm chi phí đầu tư bản quyền phần mềm trong những trường hợp phù hợp, đồng thời vẫn bảo đảm khả năng tương thích với hạ tầng chứng thư số và USB Token đang được sử dụng tại Việt Nam.

Định hướng phát triển của dự án phù hợp với tinh thần của **Công điện số 38/CĐ-TTg của Thủ tướng Chính phủ** về việc tập trung chỉ đạo thực hiện quyết liệt các giải pháp đấu tranh, ngăn chặn, xử lý hành vi xâm phạm quyền sở hữu trí tuệ; đồng thời khuyến khích sử dụng phần mềm hợp pháp, phần mềm mã nguồn mở và các giải pháp công nghệ được cấp phép theo đúng quy định của pháp luật.

---

# ✨ Chức năng

- ✅ Ký số tài liệu PDF
- ✅ Ký số hàng loạt (Batch Signing)
- ✅ Đóng dấu hình ảnh PNG
- ✅ Xem trước PDF
- ✅ Drag & Drop
- ✅ Quản lý chứng thư số
- ✅ Hỗ trợ chuẩn PKCS#11
- ✅ Hỗ trợ Bit4id
- ✅ Hỗ trợ SafeNet
- 🚧 Native Messaging
- 🚧 Chrome Extension
- 🚧 Driver Detection
- 🚧 Setup Wizard
- 🚧 Health Check
- 🚧 Multi USB Token

---

# 📷 Giao diện

## Môi trường thử nghiệm

![](docs/screenshots/hinh1.png)

---

## Ký số PDF

![](docs/screenshots/hinh2.png)

---

## Bit4id PKI Manager

![](docs/screenshots/hinh3.png)

---

## Thông tin chứng thư số

![](docs/screenshots/hinh4.png)

---

## SafeNet Authentication Client

![](docs/screenshots/hinh5.png)

---

## Hướng dẫn cài đặt Driver

![](docs/screenshots/hinh6.png)

---

# 🔐 USB Token tương thích

| USB Token | Driver | Nhận diện | Chứng thư | Ký số |
|------------|---------|-----------|------------|--------|
| Bit4id | ✅ | ✅ | ✅ | ✅ |
| SafeNet eToken | ✅ | ✅ | ✅ | 🧪 |
| SafeNet IDPrime | 🧪 | 🧪 | 🧪 | 🧪 |
| VNPT-CA | 🚧 | 🚧 | 🚧 | 🚧 |
| Viettel-CA | 🚧 | 🚧 | 🚧 | 🚧 |
| FPT-CA | 🚧 | 🚧 | 🚧 | 🚧 |
| NewCA | 🚧 | 🚧 | 🚧 | 🚧 |

---

# 🏗 Kiến trúc hệ thống

```
                        Desktop Application
                               │
                               ▼
                          GUI (Tkinter)
                               │
                               ▼
                        Core Application
                               │
          ┌────────────────────┴────────────────────┐
          ▼                                         ▼
     PDF Engine                              PKCS#11 Engine
          │                                         │
          ▼                                         ▼
   Certificate Manager                      Driver Manager
          │                                         │
          └────────────────────┬────────────────────┘
                               ▼
                          USB Token Layer
                               │
        ┌───────────────┬───────────────┬───────────────┐
        ▼               ▼               ▼
      Bit4id        SafeNet        Other Tokens
                               │
                               ▼
                    Native Messaging Host
                               │
                               ▼
                      Chrome Extension
                               │
                               ▼
                  Web Applications / eGovernment
```

---

# 📂 Cấu trúc Project

```
VGCA_XeOnline/

├── build_deb/
├── chrome-extension/
├── core/
├── docs/
│   ├── images/
│   └── screenshots/
├── gui/
├── native/
├── main.py
├── native_host.py
├── requirements.txt
├── README.md
└── vgca_xeonline.spec
```

---

# 🚀 Cài đặt

```bash
git clone https://github.com/TranManhHungDNO/VGCA_XeOnline.git

cd VGCA_XeOnline

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

python main.py
```

---

# 🧪 Kiểm thử

Đã kiểm thử trên:

- Linux Mint
- Ubuntu
- VMware Workstation
- Bit4id PKI Manager
- SafeNet Authentication Client
- PDF Signing
- PKCS#11

---

# 📚 Tài liệu

| Tài liệu | Mô tả |
|----------|------|
| docs/ARCHITECTURE.md | Kiến trúc hệ thống |
| docs/ROADMAP.md | Kế hoạch phát triển |
| docs/CHANGELOG.md | Nhật ký thay đổi |
| docs/TEST_REPORT.md | Kết quả kiểm thử |
| docs/BUGS.md | Danh sách lỗi |
| docs/COMPATIBILITY.md | Khả năng tương thích USB Token |
| docs/SETUP.md | Hướng dẫn cài đặt |
| docs/PKCS11.md | PKCS#11 Developer Guide |

---

# 🗺 Roadmap

### Version 0.9

- Linux Baseline
- PDF Signing
- Bit4id
- SafeNet

### Version 0.91

- SafeNet Compatibility

### Version 0.92

- Multiple USB Token

### Version 0.95

- Driver Detection
- PKCS#11 Refactoring
- Setup Wizard

### Version 0.96

- Native Messaging
- Chrome Extension
- Health Check

### Version 1.0

- Stable Release
- Multi Platform
- Open API
- Linux Digital Signature Platform

---

# 🤝 Đóng góp

Hiện tại dự án đang trong giai đoạn phát triển nội bộ. Mọi ý kiến đóng góp, phản hồi và đề xuất cải tiến đều được ghi nhận để hoàn thiện nền tảng trong các phiên bản tiếp theo.

---

# 📄 Giấy phép

Dự án hiện được phát triển dưới hình thức **Private Repository**.

---

<div align="center">

# VGCA XeOnline

### Bringing Digital Signatures to Linux

**"Mang chữ ký số đến với hệ điều hành mã nguồn mở."**

Made with ❤️ in Vietnam 🇻🇳

</div>
