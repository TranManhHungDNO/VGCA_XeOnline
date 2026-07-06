<div align="center">

<img src="docs/images/logo.png" width="180">

# VGCA XeOnline

### Linux Digital Signature Platform

**Offline PDF Signing • PKCS#11 • USB Token • Chrome Extension • Native Messaging**

Linux Mint • Ubuntu • Python • PDF • PKCS#11

---

</div>

# 📑 Mục lục

- [📖 Giới thiệu](#-giới-thiệu)
- [✨ Tính năng](#-tính-năng)
- [📷 Hình ảnh](#-hình-ảnh)
- [🔐 USB Token hỗ trợ](#-usb-token-hỗ-trợ)
- [🏗 Kiến trúc](#-kiến-trúc)
- [📂 Cấu trúc Project](#-cấu-trúc-project)
- [🚀 Cài đặt](#-cài-đặt)
- [📚 Tài liệu](#-tài-liệu)
- [🧪 Kiểm thử](#-kiểm-thử)
- [🗺 Roadmap](#-roadmap)
- [📋 Nhật ký thay đổi](#-nhật-ký-thay-đổi)
- [👨‍💻 Tác giả](#-tác-giả)

---

# 📖 Giới thiệu

VGCA XeOnline là nền tảng ký số PDF dành cho Linux, hỗ trợ USB Token thông qua chuẩn PKCS#11.

Mục tiêu của dự án là xây dựng một giải pháp ký số hoạt động hoàn toàn Offline, hỗ trợ nhiều USB Token và dễ dàng triển khai trên Linux Mint, Ubuntu.

---

# ✨ Tính năng

- ✅ Ký PDF
- ✅ Ký hàng loạt
- ✅ Đóng dấu PNG
- ✅ Preview PDF
- ✅ PKCS#11
- ✅ Drag & Drop
- 🚧 Multi Token
- 🚧 Setup Wizard
- 🚧 Health Check

---

# 📷 Hình ảnh

## Giao diện chính

![](docs/screenshots/hinh1.png)

---

## Ký PDF

![](docs/screenshots/hinh2.png)

---

## Bit4id Manager

![](docs/screenshots/hinh3.png)

---

## Chứng thư số

![](docs/screenshots/hinh4.png)

---

## SafeNet Client

![](docs/screenshots/hinh5.png)

---

## Wizard cài Driver

![](docs/screenshots/hinh6.png)

---

# 🔐 USB Token hỗ trợ

| Token | Driver | Scan | Load Cert | Sign |
|--------|--------|------|-----------|------|
| Bit4id | ✅ | ✅ | ✅ | ✅ |
| SafeNet eToken | ✅ | ✅ | ✅ | 🧪 |
| SafeNet IDPrime | 🧪 | 🧪 | 🧪 | 🧪 |
| VNPT | 🚧 | 🚧 | 🚧 | 🚧 |
| Viettel | 🚧 | 🚧 | 🚧 | 🚧 |

---

# 🏗 Kiến trúc

```text
GUI
 │
 ▼
Core Services
 │
 ├────────────┐
 ▼            ▼
PDF      PKCS#11 Engine
               │
               ▼
       Driver Manager
               │
     ┌─────────┴─────────┐
     ▼                   ▼
 Bit4id             SafeNet
```

👉 Xem chi tiết:

- 📄 [ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

# 📂 Cấu trúc Project

```text
VGCA_XeOnline/

├── build_deb/
├── chrome-extension/
├── core/
├── docs/
├── gui/
├── native/
├── main.py
├── README.md
└── requirements.txt
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

# 📚 Tài liệu

| Tài liệu | Nội dung |
|-----------|----------|
| 📄 [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Kiến trúc hệ thống |
| 📄 [ROADMAP.md](docs/ROADMAP.md) | Kế hoạch phát triển |
| 📄 [CHANGELOG.md](docs/CHANGELOG.md) | Nhật ký cập nhật |
| 📄 [TEST_REPORT.md](docs/TEST_REPORT.md) | Kết quả kiểm thử |
| 📄 [BUGS.md](docs/BUGS.md) | Danh sách lỗi |
| 📄 [COMPATIBILITY.md](docs/COMPATIBILITY.md) | Tương thích USB Token |

---

# 🧪 Kiểm thử

Đã kiểm thử:

- ✅ Linux Mint 22.3
- ✅ Ubuntu 24.04
- ✅ VMware Workstation
- ✅ Bit4id
- ✅ SafeNet
- ✅ PDF Signing
- ✅ PKCS#11

Chi tiết:

➡️ [TEST_REPORT.md](docs/TEST_REPORT.md)

---

# 🗺 Roadmap

| Version | Trạng thái |
|----------|------------|
| v0.9 | ✅ Linux Baseline |
| v0.91 | 🚧 SafeNet |
| v0.92 | 🚧 Multi Token |
| v0.95 | 🚧 Setup Wizard |
| v1.0 | 🎯 Stable |

Chi tiết:

➡️ [ROADMAP.md](docs/ROADMAP.md)

---

# 📋 Nhật ký thay đổi

➡️ [CHANGELOG.md](docs/CHANGELOG.md)

---

# 📈 Thống kê

- Python
- Tkinter
- PKCS#11
- PyHanko
- PyMuPDF

---

# 👨‍💻 Tác giả

**TranManhHungDNO**

VGCA XeOnline Project

---

<div align="center">

Made with ❤️ in Vietnam 🇻🇳

</div>
