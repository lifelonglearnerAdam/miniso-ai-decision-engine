import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const outputs = path.join(root, "outputs");
fs.mkdirSync(outputs, { recursive: true });

function parseCsvLine(line) {
  const cells = [];
  let value = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      if (quoted && line[i + 1] === '"') {
        value += '"';
        i += 1;
      } else {
        quoted = !quoted;
      }
    } else if (ch === "," && !quoted) {
      cells.push(value);
      value = "";
    } else {
      value += ch;
    }
  }
  cells.push(value);
  return cells;
}

function parseVisibleCount(value) {
  const text = String(value || "").trim();
  if (!text || text === "赞") return "";
  if (text.endsWith("万")) return String(Math.round(Number(text.slice(0, -1)) * 10000));
  return /^\d+$/.test(text) ? text : "";
}

function inferCategory(text) {
  if (/招聘|招人|实习|兼职|日薪|时薪/.test(text)) return "非消费反馈";
  if (/道歉|偷窥|会员|营销|广告|女性|姨妈/.test(text)) return "品牌与服务";
  if (/彩妆|唇釉|指甲油|粉底|腮红|眼线|睫毛|护肤|化妆/.test(text)) return "彩妆个护";
  if (/香水|香薰|香氛|苹果香|扩香/.test(text)) return "香氛";
  if (/零食|必吃|魔芋|糖|果冻|饼干/.test(text)) return "食品";
  if (/风扇|耳机|充电|数据线|LED|数码/.test(text)) return "数码小电";
  if (/门店|开业|FRIENDS|LAND|中央大街|横琴|探店/.test(text)) return "门店体验";
  if (/盲盒|联名|chiikawa|三丽鸥|Hello Kitty|Kitty|Jennie|森贝儿|轻松小熊|角落生物|拓麻歌子|玩具总动员|史迪仔|柯南|IP/.test(text)) return "IP潮玩";
  if (/旅行|养生|日用品|好物|必买|清单|回购|杯|伞|毛巾|生活/.test(text)) return "生活日用";
  if (/99-40|99-65|优惠|券|凑单/.test(text)) return "促销与价格";
  return "综合/其他";
}

function inferSentiment(text) {
  if (/道歉|翻车|偷窥|背刺|失望|垃圾|低质量|拒绝|不接受|抄袭|裂|坏|断货|没货|不咋好|陌生|踩雷|贵|昂贵|不值|糟糕|poor|trash|fake|defect|broken|rude|disappoint/i.test(text)) return "负向";
  if (/好物|必买|回购|喜欢|可爱|萌|好看|满意|快乐|值得|强推|好用|夯|爱|great|love|good quality|well-priced/i.test(text)) return "正向";
  if (/测评|二选一|到底|还是|求|如何|怎么样|现况|对比|争议|困惑|真假|real or fake/i.test(text)) return "混合/待判断";
  return "中性";
}

function inferTheme(text, category) {
  if (/招聘|招人|实习|兼职|日薪|时薪/.test(text)) return "检索噪声/雇主品牌";
  if (/99-40|99-65|优惠|券|凑单/.test(text)) return "促销门槛与价格敏感";
  if (/会员/.test(text)) return "结账摩擦与会员规则";
  if (/道歉|偷窥|背刺|女性|姨妈|营销|广告/.test(text)) return "品牌价值观与内容审核";
  if (/断货|补货|排队|库存|预约|限量|黄牛/.test(text)) return "可获得性与库存透明";
  if (/抄袭|MUJI|真假|fake|real|authentic/i.test(text)) return "原创性/真伪信任";
  if (/质量|做工|掉|坏|裂|漏|defect|broken|trash|low quality/i.test(text)) return "质量与耐用性";
  if (/回购|必买|清单|推荐|好物|满意/.test(text)) return "高频使用与复购价值";
  if (/价格|贵|便宜|平价|均价|20r|10块|百元|well-priced|overpriced/i.test(text)) return "性价比与价格锚点";
  if (category === "门店体验") return "门店分级与逛店体验";
  if (category === "IP潮玩") return "角色偏好与IP情绪价值";
  if (category === "香氛") return "香型偏好与预期管理";
  if (category === "彩妆个护") return "效果、色号与新手友好";
  if (category === "食品") return "口味发现与榜单需求";
  return "产品发现与购买决策";
}

function inferJourney(theme, category) {
  if (/库存|补货|排队|获得/.test(theme)) return "购买前/到店";
  if (/结账|会员|促销/.test(theme)) return "购买中";
  if (/售后|质量|耐用|真伪/.test(theme)) return "使用后/售后";
  if (category === "门店体验") return "到店体验";
  return "发现/比较";
}

function inferOpportunity(theme, category) {
  if (/库存/.test(theme)) return "区域-门店-角色级库存热力与补货预警";
  if (/会员/.test(theme)) return "统一会员规则并在结账前解释限制";
  if (/促销/.test(theme)) return "促销规则模拟器与可解释凑单方案";
  if (/质量/.test(theme)) return "高风险SKU质量红线与上市前压力测试";
  if (/真伪/.test(theme)) return "包装防伪、授权标识与售后闭环";
  if (/品牌价值观/.test(theme)) return "营销内容安全审查Agent";
  if (/价格/.test(theme)) return "价格带-功能价值联合测试";
  if (/门店/.test(theme)) return "店型承诺、货盘与陈列一致性检查";
  if (category === "IP潮玩") return "按角色而非系列预测需求";
  if (category === "香氛") return "香型描述标准化与小样/试闻验证";
  if (category === "彩妆个护") return "色号、肤质与新手任务场景共创";
  if (category === "食品") return "口味投票与小批量区域试销";
  return "高频任务型单品池与复购验证";
}

const detailOverlays = {
  "69f205bb000000001a035cbb": { summary: "标题表达品牌价格/定位变化；评论同时提到价格上涨、质量尚可、应急购买便利和生活用品齐全。", comment_theme: "价格变贵但质量/便利可抵消；用户频繁询价；应急一站购价值突出", metrics: "点赞282;收藏60;评论9", sentiment: "混合/待判断", severity: 3, category: "生活日用", theme: "性价比与价格锚点", opportunity: "价格带-功能价值联合测试" },
  "692547cb000000001e039226": { summary: "均价约20元的名创彩妆集中测评，关注是否真正好用而非仅便宜。", comment_theme: "评论未稳定加载；以正文和互动量作为证据", metrics: "点赞3333;收藏1699;评论81", sentiment: "混合/待判断", severity: 3, category: "彩妆个护", theme: "效果、色号与新手友好", opportunity: "色号、肤质与新手任务场景共创" },
  "691b121d00000000070328c1": { summary: "约200元完成全套彩妆，强调真实消费和学生党可负担。", comment_theme: "色号选择、修容下手轻重、腮红液新手门槛、完整教程需求", metrics: "点赞551;收藏340;评论34", sentiment: "正向", severity: 2, category: "彩妆个护", theme: "效果、色号与新手友好", opportunity: "色号、肤质与新手任务场景共创" },
  "688369540000000010011c90": { summary: "跨品类无限回购清单，评论围绕单价、睫毛夹、杯子、护手霜和IP设计。", comment_theme: "强询价；功能好用带来回购；IP联名好看但仍需实用", metrics: "点赞1514;收藏580;评论14", sentiment: "正向", severity: 2, category: "生活日用", theme: "高频使用与复购价值", opportunity: "高频任务型单品池与复购验证" },
  "6a1c244f000000003502498c": { summary: "均价10元左右的年度好用物，集中在彩妆、降温、出行和梳子。", comment_theme: "冰凉贴/湿巾、牙线棒、出行便携品；用户补充手机降温场景", metrics: "点赞662;收藏318;评论11", sentiment: "正向", severity: 2, category: "生活日用", theme: "高频使用与复购价值", opportunity: "高频任务型单品池与复购验证" },
  "6a0fc757000000003700c989": { summary: "Chiikawa联名到店实况，角色偏好、价格、门店地址和预约规则是主要问题。", comment_theme: "乌萨奇/小八角色偏好；69.9/99元询价；正佳广场地址；预约和到货信息", metrics: "点赞1298;收藏167;评论57", sentiment: "正向", severity: 3, category: "IP潮玩", theme: "可获得性与库存透明", opportunity: "区域-门店-角色级库存热力与补货预警" },
  "6a0096d5000000003700c839": { summary: "Hello Kitty香薰盲盒四连拆，卖点叠加毛绒、录音、变色与淡香。", comment_theme: "评论未稳定加载；正文显示多感官/可玩功能提升盲盒价值", metrics: "点赞213;收藏62;评论6", sentiment: "正向", severity: 2 },
  "6a085823000000000702e0de": { summary: "苹果香全家桶以无广、淡香、夏日香氛为主要卖点。", comment_theme: "评论未稳定加载；收藏高于点赞的一半，显示购买参考价值", metrics: "点赞584;收藏326;评论20", sentiment: "正向", severity: 2 },
  "69c3bde4000000001f000d99": { summary: "开放式必买榜征集产生高密度真实使用反馈，跨耳机、浴巾、梳子、香氛、彩妆和毛绒。", comment_theme: "耳机耐用、浴巾快干、梳子长期复购、眼线笔高复购、淡香推荐、毛绒角色吸引", metrics: "点赞4351;收藏2665;评论611", sentiment: "正向", severity: 2, category: "综合/其他", theme: "高频使用与复购价值", opportunity: "高频任务型单品池与复购验证" },
  "6964d649000000001a022148": { summary: "与MUJI收纳包对比，名创价格约为一半，但做工、内衬和原创性引发争议。", comment_theme: "反对抄袭；一分钱一分货；名创19.9元价格优势；外观相似但细节有差", metrics: "点赞2872;收藏533;评论340", sentiment: "混合/待判断", severity: 4, category: "生活日用", theme: "原创性/真伪信任", opportunity: "原创设计相似性审查与差异化门槛" },
  "6a033df40000000036018774": { summary: "两款小风扇二选一，体现参数和场景比较信息不足。", comment_theme: "评论未稳定加载；需要结构化对比续航、噪音、风量和便携性", metrics: "点赞96;收藏11;评论42", sentiment: "混合/待判断", severity: 3, category: "数码小电", theme: "产品发现与购买决策", opportunity: "建立可比较的功能参数与场景验证卡" },
  "69959b00000000001b01e498": { summary: "轻松小熊与角落生物在北京MINISO FRIENDS集中陈列，互动量高。", comment_theme: "评论未稳定加载；地点和角色组合是主要传播信息", metrics: "点赞3770;收藏436;评论260", sentiment: "正向", severity: 2, category: "IP潮玩", theme: "角色偏好与IP情绪价值", opportunity: "按角色而非系列预测需求" },
  "6a5719b6000000000f0319e1": { summary: "东北首家FRIENDS试营业测评指出门店偏小、货品不够丰富、限量盲盒标识不清，体验弱于LAND。", comment_theme: "店型分级困惑；限定品/库存询问；FRIENDS与LAND货盘差异；正式开业预期", metrics: "点赞346;收藏75;评论80", sentiment: "混合/待判断", severity: 4, category: "门店体验", theme: "门店分级与逛店体验", opportunity: "店型承诺、货盘与陈列一致性检查" },
};

const seedLines = fs.readFileSync(path.join(root, "work", "xhs_seed.csv"), "utf8").trim().split(/\r?\n/);
const seedHeaders = parseCsvLine(seedLines.shift());
const xhsRows = seedLines.map((line) => Object.fromEntries(seedHeaders.map((key, index) => [key, parseCsvLine(line)[index] || ""])));

function makeBase(input) {
  const combined = [input.title, input.content_summary, input.comment_theme].filter(Boolean).join(" ");
  const category = input.category_ip || inferCategory(combined);
  const sentiment = input.sentiment || inferSentiment(combined);
  const theme = input.primary_theme || inferTheme(combined, category);
  const noise = category === "非消费反馈";
  const negative = sentiment === "负向";
  return {
    sample_id: input.sample_id,
    platform: input.platform,
    market: input.market || "中国",
    language: input.language || "中文",
    author_display: input.author_display || "",
    published_at: input.published_at || "",
    title: input.title,
    source_url: input.source_url,
    source_precision: input.source_precision || "单条内容页",
    engagement_metric: input.engagement_metric || "",
    engagement_count: input.engagement_count || "",
    content_summary: input.content_summary || input.title,
    comment_theme: input.comment_theme || "未读取评论；仅按公开标题/摘要编码",
    sentiment,
    journey: input.journey || inferJourney(theme, category),
    category_ip: category,
    primary_theme: theme,
    severity_1_5: input.severity_1_5 || (negative ? 4 : sentiment === "混合/待判断" ? 3 : 2),
    product_dev_relevance: input.product_dev_relevance || (noise ? "低" : /营销|会员|售后|质量|库存|价格|门店|效果|复购|香型|角色/.test(theme) ? "高" : "中"),
    opportunity_tag: input.opportunity_tag || inferOpportunity(theme, category),
    evidence_level: input.evidence_level || "C-搜索摘要",
    included_in_analysis: input.included_in_analysis ?? (noise ? "否" : "是"),
    collection_date: "2026-07-18",
  };
}

const rows = xhsRows.map((seed) => {
  const overlay = detailOverlays[seed.sample_id] || {};
  return makeBase({
    sample_id: `xhs-${seed.sample_id}`,
    platform: "小红书",
    author_display: seed.author,
    published_at: seed.published_at,
    title: seed.title,
    source_url: seed.source_url,
    engagement_metric: overlay.metrics ? "点赞/收藏/评论" : "搜索卡片可见点赞",
    engagement_count: overlay.metrics || parseVisibleCount(seed.likes_visible),
    content_summary: overlay.summary || seed.title,
    comment_theme: overlay.comment_theme,
    sentiment: overlay.sentiment,
    severity_1_5: overlay.severity,
    category_ip: overlay.category,
    primary_theme: overlay.theme,
    opportunity_tag: overlay.opportunity,
    evidence_level: overlay.comment_theme ? "A-详情页含公开评论" : "B-搜索结果卡片",
  });
});

const externalRows = [
  { sample_id:"bili-BV14Q4y127jm", platform:"哔哩哔哩", published_at:"2021-08-11", title:"名创优品香水红黑榜，20就能买到香奈儿平替？", source_url:"https://www.bilibili.com/video/BV14Q4y127jm/", engagement_metric:"播放量", engagement_count:"952000", content_summary:"49.9元花香款被评价过甜；39.9元系列在瓶身质感和花果/柑橘奶香上表现突出；15元滚珠香便携。", comment_theme:"以价格带和香型拆分红黑榜；平替叙事有效但需避免过度承诺", category_ip:"香氛", sentiment:"混合/待判断", evidence_level:"B-视频页摘要" },
  { sample_id:"bili-BV114411y7dz", platform:"哔哩哔哩", published_at:"2019-09-06", title:"平民窟女孩大解放｜名创优品香水全测评", source_url:"https://www.bilibili.com/video/BV114411y7dz/", engagement_metric:"播放量", engagement_count:"58000", content_summary:"一次性测评约40支、最高价不到40元，用户需求集中在平价香水与大牌替代。", comment_theme:"平价香水、全线对比和香型教育", category_ip:"香氛", sentiment:"正向", evidence_level:"B-视频页摘要" },
  { sample_id:"bili-BV1k9Z5BREKz", platform:"哔哩哔哩", published_at:"2026-02", title:"9.9元名创真赛大牌吗？神似5星酒店？", source_url:"https://www.bilibili.com/video/BV1k9Z5BREKz/", engagement_metric:"", engagement_count:"", content_summary:"15款名创香水深度测评，以9.9元和酒店香/大牌平替作为点击锚点。", comment_theme:"低价试错、场景香型、相似度验证", category_ip:"香氛", sentiment:"混合/待判断", evidence_level:"C-搜索摘要" },
  { sample_id:"bili-BV1VrY9enEmH", platform:"哔哩哔哩", published_at:"2024", title:"名创优品家的无火香薰很主观的测评", source_url:"https://www.bilibili.com/video/BV1VrY9enEmH/", engagement_metric:"", engagement_count:"", content_summary:"无火香薰主观测评，说明香氛品类需要标准化描述同时保留主观差异。", comment_theme:"香型主观性、扩香和持久度", category_ip:"香氛", sentiment:"混合/待判断", evidence_level:"C-搜索摘要" },
  { sample_id:"bili-BV1nx411j78T", platform:"哔哩哔哩", published_at:"2017-11-05", title:"测评｜名创优品的护肤品能不能用？", source_url:"https://www.bilibili.com/video/BV1nx411j78T/", engagement_metric:"播放量", engagement_count:"147000", content_summary:"一次买十余款护肤品，结论是未发现明显高价值单品，提醒低价不等于有效。", comment_theme:"配方、功效、敏感肌安全与低价预期", category_ip:"彩妆个护", sentiment:"负向", evidence_level:"B-视频页摘要" },
  { sample_id:"bili-BV1ZPN7z3Ep7", platform:"哔哩哔哩", published_at:"2025-06-18", title:"做这样的周边可以但没必要……", source_url:"https://www.bilibili.com/video/BV1ZPN7z3Ep7/", engagement_metric:"播放量", engagement_count:"113000", content_summary:"名侦探柯南联名发光盲盒的功能设计造成意外惊吓，被评价为没有必要。", comment_theme:"功能惊喜变成负面体验；联名功能必须符合角色和安全预期", category_ip:"IP潮玩", sentiment:"负向", evidence_level:"B-视频页摘要" },
  { sample_id:"bili-BV1KE411q7CG", platform:"哔哩哔哩", published_at:"2019-11-07", title:"名创优品芝麻街联名盲盒开箱", source_url:"https://www.bilibili.com/video/BV1KE411q7CG/", engagement_metric:"播放量", engagement_count:"1661", content_summary:"开箱者认为该联名盲盒外观与质量不错。", comment_theme:"联名吸引与做工正反馈", category_ip:"IP潮玩", sentiment:"正向", evidence_level:"B-视频页摘要" },
  { sample_id:"bili-BV1BXR1YiENr", platform:"哔哩哔哩", published_at:"2025-04-07", title:"183.9元端盒带走史迪仔复古邮票盲盒", source_url:"https://www.bilibili.com/video/BV1BXR1YiENr/", engagement_metric:"播放量", engagement_count:"23", content_summary:"6个不重复并含隐藏款，传播点是端盒价格、创意造型和礼赠场景。", comment_theme:"低互动推广型内容；端盒价格和不重复规则是核心", category_ip:"IP潮玩", sentiment:"正向", evidence_level:"C-低互动视频摘要" },

  { sample_id:"douyin-jennie-restock", platform:"抖音", published_at:"2026-03-27", title:"Jennie联名补货时间", source_url:"https://www.douyin.com/shipin/7621730411631085608", engagement_metric:"点赞", engagement_count:"195", content_summary:"广州补货、代购和开箱信息；消费者在15分钟选购窗口内先抢后看。", comment_theme:"热门款缺货、排队、代购、补货日期和快速决策压力", category_ip:"IP潮玩", sentiment:"混合/待判断", source_precision:"主题/聚合页含相关视频", evidence_level:"B-抖音聚合页" },
  { sample_id:"douyin-jennie-tote", platform:"抖音", published_at:"2026-03", title:"Jennie联名托特包实物与断货反馈", source_url:"https://www.douyin.com/shipin/7621730411631085608", engagement_metric:"相关视频可见点赞", engagement_count:"12000", content_summary:"排队两小时一度断货；托特包40x28cm、柔软、容量大，但没有肩带。", comment_theme:"尺寸、容量、材质、配件缺失与断货", category_ip:"IP潮玩", sentiment:"混合/待判断", source_precision:"聚合页中的相关视频，非独立URL", evidence_level:"C-聚合页摘要" },
  { sample_id:"douyin-jennie-queue", platform:"抖音", published_at:"2026-03", title:"Jennie联名线下排队与15分钟选购", source_url:"https://www.douyin.com/shipin/7621730411631085608", engagement_metric:"", engagement_count:"", content_summary:"排队约1.5小时，热门丝巾临时补货；用户偏好大容量托特包和实用耳机包。", comment_theme:"排队成本、临时补货、实用性与粉丝冲动购买", category_ip:"IP潮玩", sentiment:"混合/待判断", source_precision:"聚合页中的相关视频，非独立URL", evidence_level:"C-聚合页摘要" },
  { sample_id:"douyin-makeup-100", platform:"抖音", published_at:"2025", title:"挑战100元名创优品全套彩妆上脸大测评", source_url:"https://www.douyin.com/topic/7637656390257035300", engagement_metric:"点赞", engagement_count:"1940", content_summary:"用100元完成全套彩妆上脸，直接检验平价彩妆效果。", comment_theme:"预算约束、全套任务和上脸效果", category_ip:"彩妆个护", sentiment:"混合/待判断", source_precision:"主题页中的视频，非独立URL", evidence_level:"C-主题页摘要" },
  { sample_id:"douyin-makeup-blind", platform:"抖音", published_at:"2026", title:"名创优品盲买自营彩妆测评", source_url:"https://www.douyin.com/topic/7637656390257035300", engagement_metric:"点赞", engagement_count:"59", content_summary:"不预选具体产品，盲买自营彩妆后进行真实测评。", comment_theme:"自营品牌信任、踩雷概率和低价试错", category_ip:"彩妆个护", sentiment:"混合/待判断", source_precision:"主题页中的视频，非独立URL", evidence_level:"C-主题页摘要" },
  { sample_id:"douyin-charger", platform:"抖音", published_at:"2024", title:"名创优品充电宝质量怎么样", source_url:"https://www.douyin.com/shipin/7396490448698787840", engagement_metric:"", engagement_count:"", content_summary:"将名创七千猫充电宝与罗马仕10000mAh产品对比。", comment_theme:"容量、品牌信任与数码产品质量", category_ip:"数码小电", sentiment:"混合/待判断", evidence_level:"C-搜索摘要" },

  { sample_id:"weibo-member-checkout", platform:"微博", published_at:"2026-06", title:"名创优品不是会员不能买单", source_url:"https://weibo.com/a/hot/372d3eddafd98947_0.html?type=grab", engagement_metric:"热搜页可见互动", engagement_count:"2159", content_summary:"消费者称购买普通发夹、毛巾等也被要求注册会员，年龄较大用户操作不友好。", comment_theme:"结账前强制注册、规则从限量潮玩外溢到普通商品、数字门槛", category_ip:"品牌与服务", sentiment:"负向", evidence_level:"A-微博热搜聚合" },
  { sample_id:"weibo-gender-marketing", platform:"微博", published_at:"2026-07", title:"名创优品推广视频含偷窥女性剧情引发争议", source_url:"https://weibo.com/2/detail/5320926360769318", engagement_metric:"", engagement_count:"", content_summary:"推广视频将偷窥情节娱乐化，品牌下架内容并终止合作；同帖还汇总湿厕纸用语和会员争议。", comment_theme:"女性安全、品牌价值观、内容审核和危机响应", category_ip:"品牌与服务", sentiment:"负向", evidence_level:"A-微博正文" },
  { sample_id:"weibo-apology-video", platform:"微博", published_at:"2026-07", title:"名创优品就合作博主低俗推广致歉", source_url:"https://weibo.com/2/detail/5320647039519948", engagement_metric:"视频播放", engagement_count:"415000", content_summary:"大量用户公开谴责将偷窥当作娱乐桥段，要求下架并追责。", comment_theme:"内容安全红线与公开追责", category_ip:"品牌与服务", sentiment:"负向", evidence_level:"A-微博正文" },
  { sample_id:"weibo-member-gift", platform:"微博", published_at:"2025-08", title:"时代少年团满赠物料漏掉成员形象后的致歉与换货", source_url:"https://www.weibo.com/2205447082/PETZx8sfq", engagement_metric:"", engagement_count:"", content_summary:"满赠物料遗漏一名成员形象，官方致歉并提供问题赠品更换。", comment_theme:"粉丝对具体成员完整呈现高度敏感；赠品也需要质量/内容校验", category_ip:"IP潮玩", sentiment:"负向", evidence_level:"A-品牌微博" },
  { sample_id:"weibo-chiikawa-demand", platform:"微博", published_at:"2025-03", title:"Chiikawa粉丝在品牌社媒评论区催联名", source_url:"https://weibo.com/ttarticle/p/show?id=2309405147680363119280", engagement_metric:"", engagement_count:"", content_summary:"公开文章记载粉丝在小红书评论区强烈期待Chiikawa联名，品牌随后快速预热上线。", comment_theme:"用户主动催联名、IP热点生命周期短、角色需求需要快速响应", category_ip:"IP潮玩", sentiment:"正向", evidence_level:"B-社交平台文章二手引述" },
  { sample_id:"weibo-ip-liked-not-product", platform:"微博", published_at:"2025-03", title:"消费者购买IP产品时喜欢的是IP而非产品本身", source_url:"https://weibo.com/ttarticle/p/show?id=2309405147680363119280", engagement_metric:"", engagement_count:"", content_summary:"文章指出IP溢价和低线市场务实需求存在张力，热IP并不自动等于好产品。", comment_theme:"IP吸引与产品力需要拆分评估", category_ip:"IP潮玩", sentiment:"混合/待判断", evidence_level:"B-社交平台文章分析" },

  { sample_id:"reddit-1so8vmb", platform:"Reddit", market:"海外", language:"英文", published_at:"2026-04-17", title:"The PPG Miniso blind boxes are high key trash", source_url:"https://www.reddit.com/r/blindbox/comments/1so8vmb/discussion_the_ppg_miniso_blind_boxes_are_high/", engagement_metric:"帖子赞", engagement_count:"23", content_summary:"Powerpuff Girls毛绒盲盒面部不错，但整体缝制和结构被评价为低质量。", comment_theme:"实际做工不及包装/图片；角色版本偏好；价格损失感", category_ip:"IP潮玩", sentiment:"负向", evidence_level:"A-帖子及公开评论" },
  { sample_id:"reddit-1my4sif", platform:"Reddit", market:"海外", language:"英文", published_at:"2025-08-23", title:"Disappointed with Miniso blind boxes", source_url:"https://www.reddit.com/r/MINISO/comments/1my4sif/disappointed/", engagement_metric:"帖子赞", engagement_count:"46", content_summary:"两盒税后54美元，成品质感像快餐玩具；包装和线上图片显得更高级。", comment_theme:"价格-质量错配、开盒后不可退、破损换货不确定", category_ip:"IP潮玩", sentiment:"负向", evidence_level:"A-帖子及公开评论" },
  { sample_id:"reddit-1jz1qt5", platform:"Reddit", market:"海外", language:"英文", published_at:"2025-04-14", title:"I bought a fake blind box in store", source_url:"https://www.reddit.com/r/MINISO/comments/1jz1qt5", engagement_metric:"帖子赞", engagement_count:"44", content_summary:"消费者称门店购买的Sanrio盲盒疑似假货/严重品控异常，包装有授权标但成品缺关键元素。", comment_theme:"真伪、包装防伪、门店责任和客服无响应", category_ip:"IP潮玩", sentiment:"负向", evidence_level:"A-帖子及公开评论" },
  { sample_id:"reddit-1pp4kik", platform:"Reddit", market:"海外", language:"英文", published_at:"2025-12-17", title:"Blind box fake vs real", source_url:"https://www.reddit.com/r/MINISO/comments/1pp4kik/blind_box_fake_vs_real/", engagement_metric:"帖子赞", engagement_count:"2", content_summary:"Stitch盲盒不同包装版本让消费者无法判断真伪。", comment_theme:"印刷质量、开盒拉条、防伪识别和渠道可信度", category_ip:"IP潮玩", sentiment:"混合/待判断", evidence_level:"A-帖子及公开评论" },
  { sample_id:"reddit-1pgi9zb", platform:"Reddit", market:"海外", language:"英文", published_at:"2025-12-07", title:"Is she real?", source_url:"https://www.reddit.com/r/MINISO/comments/1pgi9zb/is_she_real/", engagement_metric:"帖子赞", engagement_count:"4", content_summary:"My Melody盲盒颜色、包装与质量引发真伪判断。", comment_theme:"颜色一致性、正确包装和二手渠道风险", category_ip:"IP潮玩", sentiment:"负向", evidence_level:"A-帖子及公开评论" },
  { sample_id:"reddit-1uujyry", platform:"Reddit", market:"海外", language:"英文", published_at:"2026-07-12", title:"Can you identify the figure in a Miniso blind box?", source_url:"https://www.reddit.com/r/MINISO/comments/1uujyry/can_you_identify_the_figure_in_a_miniso_blind_box/", engagement_metric:"帖子赞", engagement_count:"0", content_summary:"用户想获得特定角色但不愿购买约30盒，认为价格高；评论讨论称重和二手购买。", comment_theme:"重复购买成本、角色定向需求、称重攻略、帽子易掉", category_ip:"IP潮玩", sentiment:"混合/待判断", evidence_level:"A-帖子及公开评论" },
  { sample_id:"reddit-1s2uakh", platform:"Reddit", market:"海外", language:"英文", published_at:"2026-03-24", title:"What does Miniso sell and is it cheap?", source_url:"https://www.reddit.com/r/MINISO/comments/1s2uakh/miniso/", engagement_metric:"帖子赞", engagement_count:"2", content_summary:"用户认为大多数品类价格合理，但盲盒偏贵；不同门店同一IP的货品完整度差异很大。", comment_theme:"可爱导致超预算；盲盒价格；门店货盘差异；生活日用发现", sentiment:"混合/待判断", evidence_level:"A-帖子及公开评论" },
  { sample_id:"reddit-1tftiz4", platform:"Reddit", market:"海外", language:"英文", published_at:"2026-05-17", title:"Is this real or a fake?", source_url:"https://www.reddit.com/r/MINISO/comments/1tftiz4/is_this_real_or_a_fake/", engagement_metric:"帖子赞", engagement_count:"8", content_summary:"Scrump公仔外观和包装标签引发真假争议，评论用购买渠道、二维码贴和包装袋判断。", comment_theme:"防伪标识不统一、渠道教育和仓库瑕疵边界", category_ip:"IP潮玩", sentiment:"混合/待判断", evidence_level:"A-帖子及公开评论" },
  { sample_id:"reddit-1ufjy58", platform:"Reddit", market:"海外", language:"英文", published_at:"2026-06-25", title:"Fake or legit Stitch?", source_url:"https://www.reddit.com/r/MINISO/comments/1ufjy58/fake_or_legit_stitch/", engagement_metric:"帖子赞", engagement_count:"2", content_summary:"自动售货机购买的Stitch颜色偏差，用户依赖原盒和授权标识判断。", comment_theme:"非门店渠道、价格异常和原盒保留", category_ip:"IP潮玩", sentiment:"混合/待判断", evidence_level:"A-帖子及公开评论" },
  { sample_id:"reddit-1t0jcyt", platform:"Reddit", market:"海外", language:"英文", published_at:"2026-05-01", title:"Which blind box brand has the best quality?", source_url:"https://www.reddit.com/r/PopMartCollectors/comments/1t0jcyt/which_blind_box_brand_has_the_best_quality/", engagement_metric:"帖子赞", engagement_count:"15", content_summary:"有用户认为近期Miniso部分Sanrio盲盒很可爱且有重量感，但价格仍高。", comment_theme:"质量可达到正向惊喜；与Pop Mart等品牌横向比较", category_ip:"IP潮玩", sentiment:"正向", evidence_level:"A-帖子及公开评论" },
  { sample_id:"reddit-1kjogi7", platform:"Reddit", market:"海外", language:"英文", published_at:"2025-05-11", title:"Blind box manufacture error", source_url:"https://www.reddit.com/r/MINISO/comments/1kjogi7", engagement_metric:"帖子赞", engagement_count:"35", content_summary:"Baby Three随机脸部组合被误认为制造错误，后由社区解释为产品规则。", comment_theme:"规则说明不足会被误判为品控问题", category_ip:"IP潮玩", sentiment:"混合/待判断", evidence_level:"A-帖子及公开评论" },
  { sample_id:"reddit-1ri69ve", platform:"Reddit", market:"海外", language:"英文", published_at:"2026-03", title:"Miniso Kuromi", source_url:"https://www.reddit.com/r/MINISO/comments/1ri69ve/miniso_kuromi/", engagement_metric:"", engagement_count:"", content_summary:"用户喜欢Kuromi盲盒，但认为TopToy生产质量明显更高。", comment_theme:"同集团/竞品质量对比", category_ip:"IP潮玩", sentiment:"混合/待判断", evidence_level:"B-搜索摘要" },

  { sample_id:"tp-2026-07-07", platform:"Trustpilot", market:"海外", language:"英文", published_at:"2026-07-07", title:"Blind box sold without explaining random/final-sale rules", source_url:"https://www.trustpilot.com/review/www.miniso.com", engagement_metric:"星级", engagement_count:"1", content_summary:"为6岁儿童购买公主娃娃时未被告知是随机盲盒且不可退，开出形象令儿童害怕。", comment_theme:"导购不解释盲盒规则、年龄适配和最终销售政策", category_ip:"IP潮玩", sentiment:"负向", evidence_level:"A-公开评价页" },
  { sample_id:"tp-2026-06-30", platform:"Trustpilot", market:"海外", language:"英文", published_at:"2026-06-30", title:"Faulty charging cord not replaced", source_url:"https://www.trustpilot.com/review/www.miniso.com", engagement_metric:"星级", engagement_count:"1", content_summary:"长期顾客购买的充电线有一条失效，但因无盒无票被拒换。", comment_theme:"低价电子品故障、凭证要求和门店换货", category_ip:"数码小电", sentiment:"负向", evidence_level:"A-公开评价页" },
  { sample_id:"tp-2026-06-28", platform:"Trustpilot", market:"海外", language:"英文", published_at:"2026-06-28", title:"Bottle straw fell off and bottle cracked", source_url:"https://www.trustpilot.com/review/www.miniso.com", engagement_metric:"星级", engagement_count:"1", content_summary:"水杯购买数分钟后吸管掉落并出现裂纹，门店拒绝处理。", comment_theme:"结构耐用性、即时故障和责任归属", category_ip:"生活日用", sentiment:"负向", evidence_level:"A-公开评价页" },
  { sample_id:"tp-2026-06-13", platform:"Trustpilot", market:"海外", language:"英文", published_at:"2026-06-13", title:"HQ turned a sour experience sweet", source_url:"https://www.trustpilot.com/review/www.miniso.com", engagement_metric:"星级", engagement_count:"5", content_summary:"杯子7天内变形且门店拒换，总部介入后完成更换并挽回常客。", comment_theme:"总部补救能恢复信任，但门店执行不一致", category_ip:"生活日用", sentiment:"混合/待判断", evidence_level:"A-公开评价页" },
  { sample_id:"tp-2026-06-08", platform:"Trustpilot", market:"海外", language:"英文", published_at:"2026-06-08", title:"Helpful store employees", source_url:"https://www.trustpilot.com/review/www.miniso.com", engagement_metric:"星级", engagement_count:"5", content_summary:"Wellington门店员工积极帮助顾客。", comment_theme:"现场服务正反馈", category_ip:"门店体验", sentiment:"正向", evidence_level:"A-公开评价页" },
  { sample_id:"tp-2026-06-06", platform:"Trustpilot", market:"海外", language:"英文", published_at:"2026-06-06", title:"Earbuds disconnect and die", source_url:"https://www.trustpilot.com/review/www.miniso.com", engagement_metric:"星级", engagement_count:"1", content_summary:"耳机充电后播放数分钟即反复断连，左右耳先后没电。", comment_theme:"连接稳定性与续航失效", category_ip:"数码小电", sentiment:"负向", evidence_level:"A-公开评价页" },
  { sample_id:"tp-2026-03-23", platform:"Trustpilot", market:"海外", language:"英文", published_at:"2026-03-23", title:"No customer-service response for two months", source_url:"https://www.trustpilot.com/review/www.miniso.com", engagement_metric:"星级", engagement_count:"1", content_summary:"连续三次联系支持，两个月无回复。", comment_theme:"客服不可达和售后响应时效", category_ip:"品牌与服务", sentiment:"负向", evidence_level:"A-公开评价页" },
  { sample_id:"tp-2026-03-05", platform:"Trustpilot", market:"海外", language:"英文", published_at:"2026-03-05", title:"Online order marked shipped without tracking", source_url:"https://www.trustpilot.com/review/www.miniso.com", engagement_metric:"星级", engagement_count:"1", content_summary:"线上订单无追踪且迟迟未到，多次提交客服表单无回应。", comment_theme:"物流透明度、在线客服和退款路径", category_ip:"品牌与服务", sentiment:"负向", evidence_level:"A-公开评价页" },
  { sample_id:"tp-2026-01-11", platform:"Trustpilot", market:"海外", language:"英文", published_at:"2026-01-11", title:"Membership points could not be added after payment", source_url:"https://www.trustpilot.com/review/www.miniso.com", engagement_metric:"星级", engagement_count:"2", content_summary:"结账前未解释会员积分，付款后无法补登，线上库存也被评价为不足。", comment_theme:"会员引导时机、积分补登和线上库存", category_ip:"品牌与服务", sentiment:"负向", evidence_level:"A-公开评价页" },
  { sample_id:"tp-2025-12-14", platform:"Trustpilot", market:"海外", language:"英文", published_at:"2025-12-14", title:"Store did not follow its return policy", source_url:"https://www.trustpilot.com/review/www.miniso.com", engagement_metric:"星级", engagement_count:"1", content_summary:"收据和店内政策写明7天内可退未开封商品，但经理仍拒绝。", comment_theme:"书面政策与门店执行不一致", category_ip:"品牌与服务", sentiment:"负向", evidence_level:"A-公开评价页" },
  { sample_id:"tp-2025-12-19", platform:"Trustpilot", market:"海外", language:"英文", published_at:"2025-12-19", title:"No order confirmation or customer-service response", source_url:"https://www.trustpilot.com/review/www.miniso.com", engagement_metric:"星级", engagement_count:"1", content_summary:"葡萄牙线上订单支付后无确认邮件，电话和邮件均无响应。", comment_theme:"订单确认、客服可达性和跨市场履约", category_ip:"品牌与服务", sentiment:"负向", evidence_level:"A-公开评价页" },
  { sample_id:"tp-2025-10-17", platform:"Trustpilot", market:"海外", language:"英文", published_at:"2025-10-17", title:"Franchise locations not connected for returns", source_url:"https://www.trustpilot.com/review/www.miniso.com", engagement_metric:"星级", engagement_count:"1", content_summary:"消费者称不同加盟门店系统不互通，许多商品不可退。", comment_theme:"加盟门店售后割裂和跨店退换", category_ip:"品牌与服务", sentiment:"负向", evidence_level:"B-评价页摘要" },

  { sample_id:"google-hcm-1", platform:"Google Reviews/Wanderlog", market:"越南", language:"英文", published_at:"2025-10-18", title:"Good store great service", source_url:"https://wanderlog.com/place/details/6421998/miniso", engagement_metric:"星级", engagement_count:"5", content_summary:"门店服务良好。", comment_theme:"服务正反馈", category_ip:"门店体验", sentiment:"正向", evidence_level:"B-Google评价聚合" },
  { sample_id:"google-hcm-2", platform:"Google Reviews/Wanderlog", market:"越南", language:"英文", published_at:"2018-06-09", title:"Cute goods but slightly higher price", source_url:"https://wanderlog.com/place/details/6421998/miniso", engagement_metric:"星级", engagement_count:"4", content_summary:"商品可爱，但价格略高于其他门店。", comment_theme:"可爱溢价与价格敏感", category_ip:"综合/其他", sentiment:"混合/待判断", evidence_level:"B-Google评价聚合" },
  { sample_id:"google-hcm-3", platform:"Google Reviews/Wanderlog", market:"越南", language:"英文", published_at:"2023-07-01", title:"I love this cute store", source_url:"https://wanderlog.com/place/details/6421998/miniso", engagement_metric:"星级", engagement_count:"5", content_summary:"可爱陈列带来强门店喜爱。", comment_theme:"视觉吸引和逛店愉悦", category_ip:"门店体验", sentiment:"正向", evidence_level:"B-Google评价聚合" },
  { sample_id:"bbb-2024-01-21", platform:"BBB Reviews", market:"美国", language:"英文", published_at:"2024-01-21", title:"Defective toy exchange refused", source_url:"https://www.bbb.org/us/ny/new-york/profile/department-stores/miniso-usa-0121-87160501/customer-reviews", engagement_metric:"星级", engagement_count:"1", content_summary:"购买不到24小时的破损玩具被拒绝换货，门店称问题属于公司而非门店。", comment_theme:"缺陷品、7天政策和门店责任推诿", category_ip:"IP潮玩", sentiment:"负向", evidence_level:"A-公开评价页" },
  { sample_id:"bbb-2024-05-09", platform:"BBB Reviews", market:"美国", language:"英文", published_at:"2024-05-09", title:"Return policy on receipt not honored", source_url:"https://www.bbb.org/us/ny/new-york/profile/department-stores/miniso-usa-0121-87160501/customer-reviews", engagement_metric:"星级", engagement_count:"1", content_summary:"消费者按收据退货政策操作仍被拒，且无法获得上级联系方式。", comment_theme:"退货规则执行和升级投诉路径", category_ip:"品牌与服务", sentiment:"负向", evidence_level:"A-公开评价页" },
];

for (const item of externalRows) rows.push(makeBase(item));

const fields = [
  "sample_id","platform","market","language","author_display","published_at","title","source_url","source_precision",
  "engagement_metric","engagement_count","content_summary","comment_theme","sentiment","journey","category_ip","primary_theme",
  "severity_1_5","product_dev_relevance","opportunity_tag","evidence_level","included_in_analysis","collection_date"
];

const csvEscape = (value) => `"${String(value ?? "").replaceAll('"', '""').replaceAll("\r", " ").replaceAll("\n", " ")}"`;
const csv = [fields.join(","), ...rows.map((row) => fields.map((field) => csvEscape(row[field])).join(","))].join("\n") + "\n";
fs.writeFileSync(path.join(outputs, "miniso_voc_dataset.csv"), csv, "utf8");

const comments = Object.entries(detailOverlays).map(([id, value]) => ({
  sample_id: `xhs-${id}`,
  source_url: `https://www.rednote.com/explore/${id}`,
  content_summary: value.summary,
  comment_theme: value.comment_theme,
  engagement_visible: value.metrics,
  evidence_level: "A-详情页含公开评论",
}));
const commentFields = Object.keys(comments[0]);
const commentCsv = [commentFields.join(","), ...comments.map((row) => commentFields.map((field) => csvEscape(row[field])).join(","))].join("\n") + "\n";
fs.writeFileSync(path.join(outputs, "miniso_xhs_comment_evidence.csv"), commentCsv, "utf8");

const included = rows.filter((row) => row.included_in_analysis === "是");
const countBy = (field) => Object.fromEntries([...new Set(included.map((row) => row[field]))].sort().map((value) => [value, included.filter((row) => row[field] === value).length]));
const summary = {
  generated_at: "2026-07-18",
  total_rows: rows.length,
  included_rows: included.length,
  excluded_rows: rows.length - included.length,
  by_platform: countBy("platform"),
  by_sentiment: countBy("sentiment"),
  by_category: countBy("category_ip"),
  by_theme: countBy("primary_theme"),
  high_relevance_rows: included.filter((row) => row.product_dev_relevance === "高").length,
  severe_rows: included.filter((row) => Number(row.severity_1_5) >= 4).length,
  xhs_detail_comment_rows: comments.length,
  note: "占比仅描述本次目的性公开样本，不代表总体消费者比例。",
};
fs.writeFileSync(path.join(outputs, "miniso_voc_summary.json"), JSON.stringify(summary, null, 2) + "\n", "utf8");

const codebook = `field,description,type_or_values\n` + [
  ["sample_id","稳定样本ID","text"],
  ["platform","公开来源平台","小红书/哔哩哔哩/抖音/微博/Reddit/Trustpilot/Google Reviews/BBB"],
  ["market","样本市场","中国/海外/具体国家"],
  ["title","公开内容标题或评价短标题","text"],
  ["source_url","可回溯公开链接","URL"],
  ["source_precision","链接粒度","单条内容页/主题页/评价聚合页"],
  ["engagement_metric","页面可见互动口径","点赞/播放/星级等"],
  ["engagement_count","采集时可见互动量；不同平台不可直接横比","number_or_text"],
  ["content_summary","对正文或搜索摘要的中文压缩","researcher_paraphrase"],
  ["comment_theme","公开评论主题归纳；非逐字评论","researcher_paraphrase"],
  ["sentiment","AI辅助后人工规则复核的情绪","正向/中性/负向/混合或待判断"],
  ["journey","用户旅程位置","发现比较/购买前到店/购买中/使用后售后"],
  ["category_ip","品类或IP域","controlled_vocabulary"],
  ["primary_theme","主问题/需求主题","controlled_vocabulary"],
  ["severity_1_5","对购买与信任的影响程度","1低-5高"],
  ["product_dev_relevance","对产品开发决策的相关性","低/中/高"],
  ["opportunity_tag","可进入决策引擎的机会标签","text"],
  ["evidence_level","证据等级","A详情/正文+评论; B正文或聚合; C搜索摘要"],
  ["included_in_analysis","是否进入洞察统计","是/否"],
  ["collection_date","采集日期","YYYY-MM-DD"],
].map((row) => row.map(csvEscape).join(",")).join("\n") + "\n";
fs.writeFileSync(path.join(outputs, "miniso_voc_codebook.csv"), codebook, "utf8");

console.log(JSON.stringify(summary, null, 2));
