<div align="center">

# Haxe-IDE
<img width=90% src="https://github.com/Davvex87/haxe-ide/blob/main/res/app.png?raw=true">

[![Haxe](https://img.shields.io/badge/Available%20On-haxelib-orange.svg)](https://haxe.org/)
![OS support](https://img.shields.io/badge/OS-Linux%20Windows-red)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-green.svg)](haxelib.json)

</div>

---

A small TUI application for composing and testing Haxe workspaces. It provides a code editor, project options, and a terminal-like output area so you can quickly prototype Haxe modules and run them locally.<br>
[**_Showcase video_**](https://github.com/Davvex87/haxe-ide/blob/main/res/showcase-video.mp4)

## ✨ Features

- Lightweight TUI based application built with Textual
- Manage modules, Haxe targets, and libraries
- Run and view workspace output inside the app
- Binaries for Windows and Linux

## 🚀 Installation


### Installing from haxelib (easy, cross, **recommended**):

```sh
haxelib --global install haxe-ide
haxelib --global run haxe-ide setup
haxe-ide
```

### Manual install

Standalone binaries for Windows and Linux (x86_64 only) can be found in the [Releases page](https://github.com/Davvex87/haxe-ide/releases).

#### For Windows:

- Download the .exe executable
- Copy or move it to your `HaxeToolkit/haxe` folder (`C:\\HaxeToolkit\\haxe`)

#### For Linux:

- Download the ELF executable
- Copy or move it to your local bin folder (`/usr/local/bin/`)
- chmod it with `chmod +x haxe-ide`



## 🏗️ Building from Source

Building a standalone Linux binary with PyInstaller:

```sh
chmod +x scripts/build.sh
./scripts/build.sh
```

Building on Windows using PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build.ps1
```

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Submit a pull request with a clear description