<div align="center">

<img src="docs/images/logo.png" width="180">

# VGCA XeOnline

### Linux Digital Signature Platform

Open-source digital signature platform for Linux based on PKCS#11.

![Platform](https://img.shields.io/badge/Platform-Linux-success)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active%20Development-orange)

---

**PKCS#11 • PDF Signing • USB Token • Native Messaging • Chrome Extension**

*"Bringing Digital Signatures to Linux."*

</div>

---

# 📑 Table of Contents

- Introduction
- Why VGCA XeOnline?
- Features
- Screenshots
- Supported USB Tokens
- Architecture
- Installation
- Project Structure
- Documentation
- Roadmap
- Contributing
- License

---

# 📖 Introduction

VGCA XeOnline is an open-source Digital Signature Platform for Linux.

The project enables applications to digitally sign PDF documents using USB Tokens through the PKCS#11 standard.

Instead of being only a PDF signing tool, VGCA XeOnline is designed as a reusable digital signature platform that can integrate with Desktop applications, Web Browsers, Native Messaging Hosts, Chrome Extensions and e-Government systems.

---

# ⭐ Why VGCA XeOnline?

✔ Native Linux Application

✔ Open Source

✔ PKCS#11 Standard

✔ Multiple USB Token Support

✔ PDF Digital Signing

✔ Certificate Management

✔ Browser Integration

✔ Designed for Digital Transformation

---

# ✨ Features

## PDF

- ✅ PDF Digital Signing
- ✅ Batch Signing
- ✅ PNG Image Stamp
- ✅ PDF Preview

## USB Token

- ✅ PKCS#11
- ✅ Bit4id
- ✅ SafeNet
- 🚧 Multi USB Token

## Browser Integration

- 🚧 Native Messaging
- 🚧 Chrome Extension

## System

- 🚧 Driver Detection
- 🚧 Setup Wizard
- 🚧 Health Check

---

# 📷 Screenshots

## Main Window

![](docs/screenshots/hinh1.png)

---

## PDF Signing

![](docs/screenshots/hinh2.png)

---

## Certificate Information

![](docs/screenshots/hinh4.png)

---

## Driver Setup

![](docs/screenshots/hinh6.png)

---

# 🔐 Supported USB Tokens

| Token | Detect | Certificate | Signing |
|---------|:------:|:-----------:|:-------:|
| Bit4id | ✅ | ✅ | ✅ |
| SafeNet eToken | ✅ | ✅ | 🧪 |
| SafeNet IDPrime | 🧪 | 🧪 | 🧪 |
| VNPT-CA | 🚧 | 🚧 | 🚧 |
| Viettel-CA | 🚧 | 🚧 | 🚧 |
| FPT-CA | 🚧 | 🚧 | 🚧 |
| NewCA | 🚧 | 🚧 | 🚧 |

---

# 🏗 Architecture

```
Desktop Application
        │
GUI (Tkinter)
        │
Core Engine
 ├── PDF Engine
 ├── PKCS#11 Engine
 ├── Certificate Manager
 ├── Driver Manager
 └── Diagnostics

        │

USB Token Layer

        │

Bit4id
SafeNet
Other Tokens

        │

Native Messaging

        │

Chrome Extension

        │

Web Applications
```

---

# 🚀 Installation

Clone repository

```bash
git clone https://github.com/TranManhHungDNO/VGCA_XeOnline.git

cd VGCA_XeOnline

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

python main.py
```

---

# 📂 Project Structure

```
VGCA_XeOnline

├── chrome-extension
├── core
├── docs
├── gui
├── native
├── build_deb
├── main.py
├── native_host.py
├── requirements.txt
├── README.md
└── vgca_xeonline.spec
```

---

# 📚 Documentation

| Document | Description |
|-----------|-------------|
| ARCHITECTURE.md | System Architecture |
| ROADMAP.md | Development Roadmap |
| CHANGELOG.md | Change History |
| TEST_REPORT.md | Testing Report |
| COMPATIBILITY.md | USB Token Compatibility |
| PKCS11.md | PKCS#11 Guide |

---

# 🧪 Tested Environment

| Platform | Status |
|-----------|:------:|
| Linux Mint | ✅ |
| Ubuntu | ✅ |
| Debian | 🧪 |
| VMware | ✅ |

---

# 🗺 Roadmap

## Completed

- [x] Linux Desktop GUI
- [x] PDF Signing
- [x] PKCS#11 Engine
- [x] Bit4id Support
- [x] SafeNet Support

## In Progress

- [ ] Multiple USB Tokens
- [ ] Driver Detection
- [ ] Setup Wizard
- [ ] Native Messaging
- [ ] Chrome Extension
- [ ] Health Check

## Future

- [ ] Firefox Extension
- [ ] REST API
- [ ] Windows Version
- [ ] macOS Version

---

# 🤝 Contributing

Contributions, ideas and bug reports are welcome.

Please open an Issue or submit a Pull Request.

---

# 📄 License

MIT License

See LICENSE for more information.

---

<div align="center">

# VGCA XeOnline

### Bringing Digital Signatures to Linux

Made with ❤️ in Vietnam 🇻🇳

</div>
