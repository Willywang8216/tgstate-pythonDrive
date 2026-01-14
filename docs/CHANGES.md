# 变更日志

## [Unreleased]

### Added
- 添加性能评估报告 ([`docs/perf-assessment.md`](perf-assessment.md))
- 添加性能测试结果记录模板 ([`docs/perf.md`](perf.md))
- 添加开发环境配置指南 ([`docs/setup.md`](setup.md))
- 添加性能测试脚本 ([`scripts/benchmark.sh`](../scripts/benchmark.sh))
- 添加 Locust 压测配置 ([`scripts/locustfile.py`](../scripts/locustfile.py))
- 添加性能测试脚本使用说明 ([`scripts/README.md`](../scripts/README.md))
- 添加 ruff 和 black 配置 ([`pyproject.toml`](../pyproject.toml))

### Changed
- 更新 [`README.md`](../README.md)，添加"开发与测试"章节
- 更新 [`requirements.txt`](../requirements.txt)，添加 ruff 和 locust 依赖

### Fixed
- N/A

## [2.0.0] - Previous Release

### Added
- 基于 FastAPI 重构项目
- 添加前端网盘页面管理文件
- 添加前端图床页面方便复制
- 添加自动识别群组内文件添加至前端网盘显示
- 添加文件分块上传支持（大文件）
- 添加 SSE 实时推送文件更新
- 添加 PicGo API 支持
- 添加密码保护功能

### Changed
- N/A

### Fixed
- N/A
