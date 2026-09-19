# 文档生成与检查

生成物不等于硬件验证。真实原理图 ERC、PCB DRC 和样板测试仍需执行。

本机建议解释器：

```sh
/Users/seron-cheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 硬件设计包/工具/generate_data.py
/Users/seron-cheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 硬件设计包/工具/generate_connections.py
/Users/seron-cheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 硬件设计包/工具/build_print.py
/Users/seron-cheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 硬件设计包/工具/build_workbook.py
/Users/seron-cheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 硬件设计包/工具/verify_package.py
```

跨机需要 Python 3.11+、reportlab、python-docx、pypdf，以及可嵌入的中文 TrueType 字体。为 build_print.py 传入 `--font /完整路径/字体.ttf`。不依赖联网即可从存档资料重建。

- `generate_data.py` 是 GPIO/逻辑接口和候选 BOM 的单一数据源；它验证完整实体脚覆盖、复用信号存在、GPIO 不重复、EXTI 无冲突和接口数。AF 数字、电气能力、保护协调不在此工具能力内。
- `generate_connections.py` 展开 15 颗已核验非 MCU 核心芯片的 310 条焊盘/EP 记录和 142 条参考外围连接。它不是包含所有未知器件的完整 CAD 网表。
- `build_print.py` 从 00～11 Markdown 构建 A4 PDF 与 DOCX，并检查关键内容。PDF 页码含封面/目录；厂商资料原始页码另计。
- `build_workbook.py` 把完整 CSV 实例导出成横向 A4 作业册，供逐焊盘/逐端/逐网人工检查。
- `verify_package.py` 复核资料摘要、全部建议网络出现在 PDF、链接与 Word 容器结构，输出检查报告。人工版面抽检另外记录。
- `render_preview.py` 渲染 PDF 单页与联系表，支持 `--pdf /完整路径/文件.pdf`；人工检查后更新打印版的版面抽检记录。
- `package_release.py` 在验证与版面检查完成后生成文件 SHA256 清单及项目根目录的 `硬件实施资料包_HW-R1.zip`；它只打包硬件设计包，不包含原项目全部文件。
- `import_st.py` 仅用于首次把已下载 `/tmp/car_g474.json`、`/tmp/car_g491.json` 的 ST GitHub API 响应解码成归档 XML；日常重建不需要运行。

禁止只编辑生成 CSV、附录、PDF 或 DOCX 而不更新源。不得把尚未获确认的连接器厂家腔号填成逻辑槽位 B01～B35，也不得把检验空白行自动勾选通过。
