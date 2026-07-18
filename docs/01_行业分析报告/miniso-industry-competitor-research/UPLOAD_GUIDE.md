# GitHub 上传指南

这个项目已经整理成可直接上传的仓库结构。原始 PDF 本身也能上传到 GitHub；本文件夹额外提供了 README、文本版和网页入口，使展示效果更专业。

## 方法一：用网页上传（最适合第一次使用 GitHub）

1. 登录 GitHub。
2. 点击右上角 **+**，选择 **New repository**。
3. Repository name 建议填写：`miniso-industry-competitor-research`。
4. 选择 **Public**（公开）或 **Private**（仅自己和受邀者可见）。不确定版权或隐私时，先选 Private。
5. 创建仓库时，建议暂时不要勾选自动生成 README，因为本项目已经包含 `README.md`。
6. 在电脑上解压下载的 ZIP。
7. 打开刚创建的仓库，点击 **Add file → Upload files**。
8. 把解压后的所有文件和文件夹拖入上传区域。请上传解压后的内容，不要只上传 ZIP 压缩包。
9. 在页面底部填写提交说明，例如：`Add MINISO industry research report`。
10. 点击 **Commit changes**。

上传后，GitHub 首页会自动显示 `README.md`。点击 `docs/miniso-industry-competitor-report.pdf` 可阅读完整报告。

## 方法二：用 Git 命令上传

先在 GitHub 创建一个空仓库，然后在终端进入解压后的项目文件夹：

```bash
cd /你的路径/miniso-industry-competitor-research

git init
git add .
git commit -m "Add MINISO industry and competitor research report"
git branch -M main
git remote add origin https://github.com/你的用户名/miniso-industry-competitor-research.git
git push -u origin main
```

把命令中的 `你的用户名` 改成你的 GitHub 用户名。

第一次使用 Git 时，可能还需要设置身份：

```bash
git config --global user.name "你的名字"
git config --global user.email "你的GitHub邮箱"
```

## 可选：发布为 GitHub Pages 网页

本项目已经包含 `index.html`。上传完成后：

1. 打开仓库的 **Settings**。
2. 在左侧找到 **Pages**。
3. 在 Build and deployment 中选择从分支部署。
4. Branch 选择 `main`，文件夹选择根目录 `/ (root)`。
5. 保存并等待部署完成。

部署完成后，GitHub 会显示网页地址。以后修改并提交 `index.html`，网页也会随之更新。

## 上传前检查

- 确认报告中没有个人隐私、客户机密或未授权材料。
- 不确定是否能公开时，先使用 Private 仓库。
- 可以在 `README.md` 中补充作者、日期、项目背景或作品集说明。
- 本项目未附加开源许可证；若要允许他人转载或修改，请先确定合适的授权方式。
