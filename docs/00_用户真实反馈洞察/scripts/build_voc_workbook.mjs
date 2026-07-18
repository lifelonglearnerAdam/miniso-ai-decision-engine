import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(import.meta.dirname, "..");
const outputs = path.join(root, "outputs");
const qaDir = path.join(root, "work", "xlsx_qa");
await fs.mkdir(qaDir, { recursive: true });

const dataCsv = await fs.readFile(path.join(outputs, "miniso_voc_dataset.csv"), "utf8");
const commentsCsv = await fs.readFile(path.join(outputs, "miniso_xhs_comment_evidence.csv"), "utf8");
const codebookCsv = await fs.readFile(path.join(outputs, "miniso_voc_codebook.csv"), "utf8");
const workbook = await Workbook.fromCSV(dataCsv, { sheetName: "样本库" });
await workbook.fromCSV(commentsCsv, { sheetName: "小红书评论证据" });
await workbook.fromCSV(codebookCsv, { sheetName: "字段说明" });
const overview = workbook.worksheets.add("概览");

const navy = "#20354D";
const red = "#C84A44";
const gold = "#D7A22A";
const teal = "#2B7A78";
const pale = "#F3F6F8";
const paleGold = "#FFF6DD";
const ink = "#1F2933";
const muted = "#66717E";

overview.showGridLines = false;
overview.getRange("A1:J1").merge();
overview.getRange("A1").values = [["MINISO 用户之声样本库 | 公开社媒多平台"]];
overview.getRange("A1:J1").format = { fill: navy, font: { bold: true, color: "#FFFFFF", size: 18 }, rowHeight: 34, verticalAlignment: "center" };
overview.getRange("A2:J2").merge();
overview.getRange("A2").values = [["目的性公开样本，仅用于产品开发假设与验证；平台互动量不可直接横向比较"]];
overview.getRange("A2:J2").format = { fill: "#E9EEF3", font: { color: muted, italic: true, size: 10 }, rowHeight: 26, verticalAlignment: "center" };

const kpiLabels = [["总样本"], ["纳入分析"], ["小红书样本"], ["研发高相关"], ["严重度≥4"]];
const kpiFormulas = [
  "=COUNTA('样本库'!$A$2:$A$125)",
  '=COUNTIF(\'样本库\'!$V$2:$V$125,"是")',
  '=COUNTIF(\'样本库\'!$B$2:$B$125,"小红书")',
  '=COUNTIFS(\'样本库\'!$V$2:$V$125,"是",\'样本库\'!$S$2:$S$125,"高")',
  '=COUNTIFS(\'样本库\'!$V$2:$V$125,"是",\'样本库\'!$R$2:$R$125,">=4")',
];
const kpiCols = ["A", "C", "E", "G", "I"];
for (let i = 0; i < kpiCols.length; i += 1) {
  const col = kpiCols[i];
  const next = String.fromCharCode(col.charCodeAt(0) + 1);
  overview.getRange(`${col}4:${next}4`).merge();
  overview.getRange(`${col}5:${next}6`).merge();
  overview.getRange(`${col}4`).values = [kpiLabels[i]];
  overview.getRange(`${col}5`).formulas = [[kpiFormulas[i]]];
  overview.getRange(`${col}4:${next}4`).format = { fill: pale, font: { bold: true, color: muted, size: 10 }, horizontalAlignment: "center", verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: "#D6DEE5" } };
  overview.getRange(`${col}5:${next}6`).format = { fill: "#FFFFFF", font: { bold: true, color: i === 4 ? red : navy, size: 20 }, horizontalAlignment: "center", verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: "#D6DEE5" } };
}

overview.getRange("A8:B8").values = [["平台", "样本数"]];
const platforms = ["小红书", "哔哩哔哩", "抖音", "微博", "Reddit", "Trustpilot", "Google Reviews/Wanderlog", "BBB Reviews"];
overview.getRange("A9:A16").values = platforms.map((value) => [value]);
overview.getRange("B9").formulas = [["=COUNTIF('样本库'!$B$2:$B$125,A9)"]];
overview.getRange("B9:B16").fillDown();

overview.getRange("D8:E8").values = [["情绪", "样本数"]];
overview.getRange("D9:D12").values = [["正向"], ["中性"], ["混合/待判断"], ["负向"]];
overview.getRange("E9").formulas = [["=COUNTIFS('样本库'!$V$2:$V$125,\"是\",'样本库'!$N$2:$N$125,D9)"]];
overview.getRange("E9:E12").fillDown();

overview.getRange("G8:H8").values = [["品类/域", "样本数"]];
const categories = ["IP潮玩", "促销与价格", "生活日用", "品牌与服务", "门店体验", "彩妆个护", "香氛", "数码小电", "食品", "综合/其他"];
overview.getRange("G9:G18").values = categories.map((value) => [value]);
overview.getRange("H9").formulas = [["=COUNTIFS('样本库'!$V$2:$V$125,\"是\",'样本库'!$P$2:$P$125,G9)"]];
overview.getRange("H9:H18").fillDown();

overview.getRange("A19:B19").values = [["主要主题", "样本数"]];
const themes = ["高频使用与复购价值", "促销门槛与价格敏感", "产品发现与购买决策", "质量与耐用性", "角色偏好与IP情绪价值", "门店分级与逛店体验", "性价比与价格锚点", "原创性/真伪信任", "效果、色号与新手友好", "可获得性与库存透明", "结账摩擦与会员规则", "香型偏好与预期管理", "品牌价值观与内容审核", "口味发现与榜单需求"];
overview.getRange("A20:A33").values = themes.map((value) => [value]);
overview.getRange("B20").formulas = [["=COUNTIFS('样本库'!$V$2:$V$125,\"是\",'样本库'!$Q$2:$Q$125,A20)"]];
overview.getRange("B20:B33").fillDown();

for (const range of ["A8:B16", "D8:E12", "G8:H18", "A19:B33"]) {
  overview.getRange(range).format = { font: { color: ink, size: 10 }, borders: { insideHorizontal: { style: "thin", color: "#E1E6EB" }, bottom: { style: "thin", color: "#C7D0D9" } } };
}
for (const range of ["A8:B8", "D8:E8", "G8:H8", "A19:B19"]) {
  overview.getRange(range).format = { fill: navy, font: { bold: true, color: "#FFFFFF", size: 10 }, horizontalAlignment: "center", verticalAlignment: "center", rowHeight: 24 };
}
overview.getRange("A20:A33").format.wrapText = true;
overview.getRange("A35:J36").merge();
overview.getRange("A35").values = [["读取口径：A=详情页正文/公开评论；B=正文或评价聚合；C=搜索摘要。统计只描述本数据集，不推断总体消费者比例。"]];
overview.getRange("A35:J36").format = { fill: paleGold, font: { color: "#6F5310", size: 10 }, wrapText: true, verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: "#E6CF86" } };

overview.getRange("A1:J36").format.font.name = "Arial";
overview.getRange("A:J").format.columnWidth = 13;
overview.getRange("A:A").format.columnWidth = 27;
overview.getRange("G:G").format.columnWidth = 20;
overview.freezePanes.freezeRows(2);

const samples = workbook.worksheets.getItem("样本库");
samples.showGridLines = false;
samples.freezePanes.freezeRows(1);
samples.freezePanes.freezeColumns(2);
samples.getRange("A1:W125").format.font = { name: "Arial", size: 9, color: ink };
samples.getRange("A1:W1").format = { fill: navy, font: { name: "Arial", size: 9, bold: true, color: "#FFFFFF" }, wrapText: true, verticalAlignment: "center", rowHeight: 34, borders: { bottom: { style: "medium", color: gold } } };
samples.getRange("A2:W125").format = { verticalAlignment: "top", borders: { insideHorizontal: { style: "thin", color: "#E8ECEF" } } };
samples.getRange("L2:M125").format.wrapText = true;
samples.getRange("T2:T125").format.wrapText = true;
samples.getRange("G2:G125").format.wrapText = true;
samples.getRange("A:A").format.columnWidth = 21;
samples.getRange("B:B").format.columnWidth = 16;
samples.getRange("C:F").format.columnWidth = 13;
samples.getRange("G:G").format.columnWidth = 34;
samples.getRange("H:H").format.columnWidth = 42;
samples.getRange("I:K").format.columnWidth = 17;
samples.getRange("L:M").format.columnWidth = 42;
samples.getRange("N:Q").format.columnWidth = 20;
samples.getRange("R:R").format.columnWidth = 12;
samples.getRange("S:S").format.columnWidth = 15;
samples.getRange("T:T").format.columnWidth = 35;
samples.getRange("U:W").format.columnWidth = 18;
samples.getRange("R2:R125").format.horizontalAlignment = "center";
samples.getRange("N2:N125").conditionalFormats.add("containsText", { text: "负向", format: { fill: "#FCE8E6", font: { color: "#A22920", bold: true } } });
samples.getRange("N2:N125").conditionalFormats.add("containsText", { text: "正向", format: { fill: "#E8F4EA", font: { color: "#1E6B3A", bold: true } } });
samples.getRange("R2:R125").conditionalFormats.add("cellIs", { operator: "greaterThanOrEqual", formula: 4, format: { fill: "#FCE8E6", font: { color: "#A22920", bold: true } } });
samples.getRange("V2:V125").conditionalFormats.add("containsText", { text: "否", format: { fill: "#ECEFF1", font: { color: muted, italic: true } } });
samples.tables.add("A1:W125", true, "VocSamplesTable").style = "TableStyleMedium2";

const comments = workbook.worksheets.getItem("小红书评论证据");
comments.showGridLines = false;
comments.freezePanes.freezeRows(1);
comments.getRange("A1:F14").format.font = { name: "Arial", size: 10, color: ink };
comments.getRange("A1:F1").format = { fill: teal, font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, rowHeight: 28 };
comments.getRange("A2:F14").format = { verticalAlignment: "top", wrapText: true, borders: { insideHorizontal: { style: "thin", color: "#E1E6EB" } } };
comments.getRange("A:A").format.columnWidth = 25;
comments.getRange("B:B").format.columnWidth = 42;
comments.getRange("C:D").format.columnWidth = 52;
comments.getRange("E:F").format.columnWidth = 24;
comments.tables.add("A1:F14", true, "XhsEvidenceTable").style = "TableStyleMedium4";

const codebook = workbook.worksheets.getItem("字段说明");
codebook.showGridLines = false;
codebook.freezePanes.freezeRows(1);
codebook.getRange("A1:C21").format.font = { name: "Arial", size: 10, color: ink };
codebook.getRange("A1:C1").format = { fill: navy, font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, rowHeight: 28 };
codebook.getRange("A2:C21").format = { verticalAlignment: "top", wrapText: true, borders: { insideHorizontal: { style: "thin", color: "#E1E6EB" } } };
codebook.getRange("A:A").format.columnWidth = 28;
codebook.getRange("B:B").format.columnWidth = 55;
codebook.getRange("C:C").format.columnWidth = 48;
codebook.tables.add("A1:C21", true, "CodebookTable").style = "TableStyleMedium2";

const chart = overview.charts.add("bar", overview.getRange("A8:B16"));
chart.title = "样本平台分布";
chart.hasLegend = false;
chart.setPosition("D20", "J33");
chart.xAxis = { axisType: "textAxis", textStyle: { fontSize: 9 } };
chart.yAxis = { numberFormatCode: "0" };

const overviewPreview = await workbook.render({ sheetName: "概览", range: "A1:J36", scale: 1.4, format: "png" });
await fs.writeFile(path.join(qaDir, "overview.png"), new Uint8Array(await overviewPreview.arrayBuffer()));
const samplePreview = await workbook.render({ sheetName: "样本库", range: "A1:M12", scale: 1.0, format: "png" });
await fs.writeFile(path.join(qaDir, "samples.png"), new Uint8Array(await samplePreview.arrayBuffer()));
const commentPreview = await workbook.render({ sheetName: "小红书评论证据", range: "A1:F8", scale: 1.0, format: "png" });
await fs.writeFile(path.join(qaDir, "comments.png"), new Uint8Array(await commentPreview.arrayBuffer()));
const codebookPreview = await workbook.render({ sheetName: "字段说明", range: "A1:C12", scale: 1.0, format: "png" });
await fs.writeFile(path.join(qaDir, "codebook.png"), new Uint8Array(await codebookPreview.arrayBuffer()));

const inspect = await workbook.inspect({ kind: "table", range: "概览!A1:J36", include: "values,formulas", tableMaxRows: 36, tableMaxCols: 10, maxChars: 10000 });
console.log(inspect.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 300 }, summary: "final formula error scan" });
console.log(errors.ndjson);

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(path.join(outputs, "miniso_voc_dataset.xlsx"));
