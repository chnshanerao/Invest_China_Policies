"""
政策生命周期科学评估框架

生命周期阶段定义（7阶段模型）:
┌─────────┬──────────┬──────────────────────────────────────────┐
│  阶段    │ 英文      │ 定义                                    │
├─────────┼──────────┼──────────────────────────────────────────┤
│ 规划期   │ Planning  │ 政策酝酿讨论，尚未正式实施                │
│ 启动期   │ Launch    │ 政策刚发布，机构组建，试点启动(0-2年)      │
│ 扩张期   │ Expansion │ 大规模投入，快速推进，政策红利释放(2-5年)   │
│ 验证期   │ Validation│ 检验成效，问题暴露，调整优化(3-7年)        │
│ 成熟期   │ Maturity  │ 制度稳定，效果显现，进入常态化(5-15+年)    │
│ 调整期   │ Adjustment│ 政策方向转型，力度变化，重新定位            │
│ 衰退期   │ Decline   │ 边际效益递减，逐步淡化或被替代             │
└─────────┴──────────┴──────────────────────────────────────────┘

执行力度评分(1-10): 资金投入/政策密度/领导层关注度/配套措施完备度
执行效果评分(1-10): GDP贡献/就业带动/产业聚集/制度创新/社会效益
"""

import os, sys, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection


def migrate_lifecycle_fields():
    conn = get_connection()
    cursor = conn.cursor()

    new_columns = [
        ("lifecycle_stage", "TEXT DEFAULT '验证期'"),
        ("lifecycle_stage_en", "TEXT DEFAULT 'Validation'"),
        ("execution_intensity", "REAL DEFAULT 5.0"),
        ("execution_effectiveness", "REAL DEFAULT 5.0"),
        ("expected_end_year", "INTEGER"),
        ("lifecycle_note", "TEXT"),
        ("policy_momentum", "TEXT DEFAULT '平稳'"),  # 加速/平稳/减速
    ]

    for col_name, col_def in new_columns:
        try:
            cursor.execute(f"ALTER TABLE policies ADD COLUMN {col_name} {col_def}")
        except sqlite3.OperationalError:
            pass  # column already exists

    conn.commit()
    conn.close()
    print("Lifecycle fields migration complete.")


# 逐一评估92个政策的生命周期
# key = policy name, value = assessment dict
LIFECYCLE_ASSESSMENTS = {
    # ==================== 国际战略 ====================
    "一带一路": {
        "stage": "调整期", "stage_en": "Adjustment",
        "intensity": 7, "effectiveness": 6, "end_year": None,
        "momentum": "减速",
        "note": "2013年启动，十年高歌猛进后进入战略收缩调整期。部分项目出现债务陷阱争议，'小而美'替代'大而全'。投资规模从峰值回落，但制度框架已成熟。"
    },
    "RCEP区域全面经济伙伴关系": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 6, "effectiveness": 7, "end_year": None,
        "momentum": "加速",
        "note": "2022年生效，关税减让持续推进中。中国对RCEP国家贸易占比稳步提升，原产地规则利用率逐年提高。处于制度红利释放期。"
    },
    "中国-东盟自贸区升级": {
        "stage": "启动期", "stage_en": "Launch",
        "intensity": 5, "effectiveness": 3, "end_year": None,
        "momentum": "加速",
        "note": "3.0版本2024年开始谈判，数字经济和绿色经济为新增重点。尚处于规则制定阶段，实质性成果待显现。"
    },

    # ==================== 区域重大战略 ====================
    "京津冀协同发展": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 7, "effectiveness": 5, "end_year": None,
        "momentum": "平稳",
        "note": "2014年启动已逾10年，交通一体化基本完成(1小时通勤圈)，产业转移效果不及预期。北京虹吸效应未根本改变，天津经济持续低迷。制度框架稳定但突破有限。"
    },
    "雄安新区": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 9, "effectiveness": 3, "end_year": None,
        "momentum": "平稳",
        "note": "2017年设立，投入超万亿但GDP仅689亿，投资效率20:1。央企总部搬迁推进中但市场化活力不足。政治力度极高但经济产出严重滞后，债务率407%。"
    },
    "长江经济带发展": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 7, "effectiveness": 7, "end_year": None,
        "momentum": "平稳",
        "note": "2014年启动，'共抓大保护'成效显著。长江水质优良断面比例从2016年82%升至2024年97%。沿线GDP占全国46%+，产业转型升级持续推进。"
    },
    "粤港澳大湾区": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 8, "effectiveness": 8, "end_year": None,
        "momentum": "加速",
        "note": "2019年规划纲要发布，深中通道2024年通车，前海/横琴/南沙政策密集。GDP超14万亿，科创走廊成型。跨境规则衔接仍为核心挑战。"
    },
    "长三角一体化发展": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 8, "effectiveness": 8, "end_year": None,
        "momentum": "加速",
        "note": "2018年升级为国家战略，示范区制度创新超120项。区域GDP超30万亿，集成电路/新能源汽车/生物医药三大产业集群全球竞争力强。一体化制度框架最为完善。"
    },
    "黄河流域生态保护和高质量发展": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 6, "effectiveness": 5, "end_year": None,
        "momentum": "平稳",
        "note": "2019年提出，生态保护为主线。水资源约束严峻，沿线多为经济欠发达地区。政策力度不及长江经济带，产业发展动力有限。"
    },
    "成渝地区双城经济圈": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 7, "effectiveness": 6, "end_year": None,
        "momentum": "加速",
        "note": "2020年提出，成渝中线高铁建设中，两地GDP合计超8万亿。电子信息、汽车产业集聚效应明显，但两城协同仍存在竞争大于合作的局面。"
    },

    # ==================== 经济特区 ====================
    "深圳经济特区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 8, "effectiveness": 10, "end_year": None,
        "momentum": "平稳",
        "note": "1980年设立，44年发展成为GDP3.68万亿的全球科创中心。特区红利已充分释放，当前以'先行示范区'新定位继续引领。最成功的中国经济实验。"
    },
    "珠海经济特区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 5, "effectiveness": 5, "end_year": None,
        "momentum": "平稳",
        "note": "1980年设立，经济体量远小于深圳。横琴粤澳深度合作区为新增长点，但整体发展后劲需借助大湾区势能。"
    },
    "汕头经济特区": {
        "stage": "衰退期", "stage_en": "Decline",
        "intensity": 3, "effectiveness": 3, "end_year": None,
        "momentum": "减速",
        "note": "1980年设立，发展长期滞后于其他特区。华侨试验区成效有限，人口外流明显。特区政策红利基本消耗殆尽。"
    },
    "厦门经济特区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 5, "effectiveness": 7, "end_year": None,
        "momentum": "平稳",
        "note": "1980年设立，发展质量较高但体量受限于面积。两岸关系紧张影响对台经贸功能发挥，但旅游、高新技术产业稳健。"
    },
    "海南经济特区": {
        "stage": "调整期", "stage_en": "Adjustment",
        "intensity": 9, "effectiveness": 5, "end_year": None,
        "momentum": "加速",
        "note": "1988年设立特区效果平平，2018年升级为自贸港后重获政策力度。2025年封关运作，正处于从特区向自贸港的战略转型关键期。"
    },
    "喀什经济特区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 4, "effectiveness": 3, "end_year": None,
        "momentum": "平稳",
        "note": "2010年设立，受地缘位置和基础设施限制，发展远不及预期。人口基数小，产业基础薄弱，主要依赖边贸和政策性投入。"
    },
    "霍尔果斯经济特区": {
        "stage": "衰退期", "stage_en": "Decline",
        "intensity": 3, "effectiveness": 2, "end_year": None,
        "momentum": "减速",
        "note": "2010年设立，曾因企业所得税五免优惠引发'注册经济'虚火。2018年后大批空壳公司注销，税收优惠收紧。口岸功能存在但开发区基本失败。"
    },

    # ==================== 国家级新区 ====================
    "上海浦东新区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 8, "effectiveness": 10, "end_year": None,
        "momentum": "平稳",
        "note": "1992年开发开放，GDP超1.8万亿，陆家嘴金融中心+张江科学城双引擎。2021年升级为'引领区'，制度型开放走在最前。中国新区最成功标杆。"
    },
    "天津滨海新区": {
        "stage": "调整期", "stage_en": "Adjustment",
        "intensity": 5, "effectiveness": 4, "end_year": None,
        "momentum": "减速",
        "note": "2006年设立，曾GDP注水被挤水三分之一。2018年后经济数据回归真实，增长乏力。港口优势被削弱，制造业升级缓慢。"
    },
    "重庆两江新区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 6, "effectiveness": 6, "end_year": None,
        "momentum": "平稳",
        "note": "2010年设立，汽车和电子信息产业集聚。GDP超4000亿但增速放缓，面临产业升级转型压力。内陆开放高地定位基本实现。"
    },
    "浙江舟山群岛新区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 5, "effectiveness": 5, "end_year": None,
        "momentum": "平稳",
        "note": "2011年设立，大宗商品储运中转基地定位清晰。绿色石化基地建成投产，但海洋经济多元化发展仍在摸索。"
    },
    "甘肃兰州新区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 5, "effectiveness": 3, "end_year": None,
        "momentum": "平稳",
        "note": "2012年设立，距主城区70公里导致产城融合困难。人口导入远低于预期，基础设施超前建设形成大量空置。西北新区普遍困境的缩影。"
    },
    "广东南沙新区": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 7, "effectiveness": 5, "end_year": None,
        "momentum": "加速",
        "note": "2012年设立，2022年国务院发布南沙方案后政策力度大增。科技创新和港澳合作为主线，但与前海/横琴存在定位竞争。"
    },
    "陕西西咸新区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 5, "effectiveness": 4, "end_year": None,
        "momentum": "平稳",
        "note": "2014年设立，西安-咸阳一体化推进缓慢。2017年托管至西安后行政理顺，但产业导入不及预期。"
    },
    "贵州贵安新区": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 6, "effectiveness": 6, "end_year": None,
        "momentum": "加速",
        "note": "2014年设立，大数据中心集群(苹果、华为、腾讯)成为核心竞争力。2020年与贵阳市融合发展后效率提升，算力经济前景看好。"
    },
    "青岛西海岸新区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 6, "effectiveness": 7, "end_year": None,
        "momentum": "平稳",
        "note": "2014年设立，GDP突破4500亿，在所有新区中经济体量排名前列。海洋经济、影视文化(东方影都)特色鲜明。"
    },
    "大连金普新区": {
        "stage": "调整期", "stage_en": "Adjustment",
        "intensity": 4, "effectiveness": 4, "end_year": None,
        "momentum": "减速",
        "note": "2014年设立，受东北整体经济下行影响明显。日韩外资撤离潮冲击加工贸易，产业转型升级动力不足。"
    },
    "四川天府新区": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 7, "effectiveness": 7, "end_year": None,
        "momentum": "加速",
        "note": "2014年设立，公园城市理念+兴隆湖科学城双核驱动。成都经济强劲增长的重要支撑，科创和高端服务业集聚效应显现。"
    },
    "湖南湘江新区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 6, "effectiveness": 6, "end_year": None,
        "momentum": "平稳",
        "note": "2015年设立，工程机械(三一、中联)和智能驾驶产业为特色。长沙经济稳健增长的主要载体。"
    },
    "南京江北新区": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 7, "effectiveness": 6, "end_year": None,
        "momentum": "加速",
        "note": "2015年设立，集成电路和生命健康产业为双主线。台积电南京工厂虽受限制但产业集群仍在扩大。"
    },
    "福州新区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 5, "effectiveness": 4, "end_year": None,
        "momentum": "平稳",
        "note": "2015年设立，两岸合作功能因政治因素受限。海洋经济和数字经济为新发力点，但与厦门的竞争分散了资源。"
    },
    "云南滇中新区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 4, "effectiveness": 3, "end_year": None,
        "momentum": "平稳",
        "note": "2015年设立，面向南亚东南亚的定位清晰但执行困难。产业基础薄弱，人才吸引力不足，与昆明主城区的融合待深化。"
    },
    "哈尔滨新区": {
        "stage": "衰退期", "stage_en": "Decline",
        "intensity": 3, "effectiveness": 2, "end_year": None,
        "momentum": "减速",
        "note": "2015年设立，东北人口外流和经济下行严重影响发展。对俄合作因地缘政治变化而不确定性增加。新区建设基本停滞。"
    },
    "长春新区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 4, "effectiveness": 4, "end_year": None,
        "momentum": "平稳",
        "note": "2016年设立，一汽智能化转型带动汽车产业升级。光电信息产业有特色但规模有限，东北振兴大环境制约发展速度。"
    },
    "江西赣江新区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 5, "effectiveness": 4, "end_year": None,
        "momentum": "平稳",
        "note": "2016年设立，绿色金融改革创新试验区为特色。新能源(锂电)产业借势发展但整体规模偏小。"
    },
    "河北雄安新区": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 9, "effectiveness": 3, "end_year": None,
        "momentum": "平稳",
        "note": "与区域战略中的雄安新区为同一政策实体，重复条目。详见区域重大战略分类下的评估。"
    },

    # ==================== 自贸试验区/港 ====================
    "中国(上海)自贸试验区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 8, "effectiveness": 9, "end_year": None,
        "momentum": "平稳",
        "note": "2013年设立，全国第一个自贸区。负面清单从190项缩减到27项，制度创新经验全国推广超300项。临港新片区2019年扩展后注入新活力。"
    },
    "中国(广东)自贸试验区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 7, "effectiveness": 7, "end_year": None,
        "momentum": "平稳",
        "note": "2015年设立(前海+横琴+南沙)，与大湾区战略深度融合。前海深港合作区扩区后面积翻倍，制度创新活跃。"
    },
    "中国(天津)自贸试验区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 5, "effectiveness": 5, "end_year": None,
        "momentum": "减速",
        "note": "2015年设立，融资租赁业务全国领先。但整体受天津经济下行影响，创新突破有限。"
    },
    "中国(福建)自贸试验区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 5, "effectiveness": 5, "end_year": None,
        "momentum": "平稳",
        "note": "2015年设立，对台经贸是特色但受两岸关系影响。海丝核心区建设稳步推进。"
    },
    "中国(辽宁)自贸试验区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 4, "effectiveness": 3, "end_year": None,
        "momentum": "减速",
        "note": "2017年设立，国企改革试验效果有限。营商环境改善缓慢，外资利用规模在所有自贸区中排名靠后。"
    },
    "中国(浙江)自贸试验区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 7, "effectiveness": 8, "end_year": None,
        "momentum": "加速",
        "note": "2017年设立，油气全产业链特色鲜明。2020年扩区至宁波、杭州、金义片区后数字贸易快速发展，是最具活力的自贸区之一。"
    },
    "中国(河南)自贸试验区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 6, "effectiveness": 6, "end_year": None,
        "momentum": "平稳",
        "note": "2017年设立，跨境电商和物流枢纽定位清晰。郑州航空港综保区业务量稳居全国前列。"
    },
    "中国(湖北)自贸试验区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 6, "effectiveness": 6, "end_year": None,
        "momentum": "平稳",
        "note": "2017年设立，光谷光电信息产业为核心。疫情后恢复良好，生物医药和芯片产业集聚。"
    },
    "中国(重庆)自贸试验区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 6, "effectiveness": 6, "end_year": None,
        "momentum": "平稳",
        "note": "2017年设立，中新互联互通+陆海新通道双重叠加。西部陆海新通道班列运量持续增长。"
    },
    "中国(四川)自贸试验区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 6, "effectiveness": 6, "end_year": None,
        "momentum": "平稳",
        "note": "2017年设立，成都双流航空港+青白江铁路港双枢纽。航空经济和中欧班列为亮点。"
    },
    "中国(陕西)自贸试验区": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 5, "effectiveness": 5, "end_year": None,
        "momentum": "平稳",
        "note": "2017年设立，一带一路核心区定位。西安中欧班列'长安号'全国领先，但服务贸易和金融创新不够突出。"
    },
    "中国(海南)自贸港": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 9, "effectiveness": 5, "end_year": None,
        "momentum": "加速",
        "note": "2018年宣布建设，2025年封关运作。零关税+低税率政策逐步落地，离岛免税年销售600亿+。封关是关键里程碑，成败将在未来5年见分晓。"
    },
    "中国(山东)自贸试验区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 6, "effectiveness": 5, "end_year": None,
        "momentum": "平稳",
        "note": "2019年设立，海洋经济和日韩合作为特色。青岛片区表现突出，但整体制度创新力度不及第一批自贸区。"
    },
    "中国(江苏)自贸试验区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 7, "effectiveness": 7, "end_year": None,
        "momentum": "加速",
        "note": "2019年设立，苏州+南京+连云港三片区。生物医药(苏州工业园)和集成电路实力雄厚，是后发但高质量的自贸区。"
    },
    "中国(广西)自贸试验区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 5, "effectiveness": 4, "end_year": None,
        "momentum": "平稳",
        "note": "2019年设立，面向东盟但受经济基础制约。钦州港和中马产业园为亮点，但整体吸引力有限。"
    },
    "中国(河北)自贸试验区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 5, "effectiveness": 4, "end_year": None,
        "momentum": "平稳",
        "note": "2019年设立，雄安+正定+曹妃甸+大兴机场四片区。与雄安新区联动发展，但尚未形成独立的制度创新亮点。"
    },
    "中国(云南)自贸试验区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 5, "effectiveness": 4, "end_year": None,
        "momentum": "平稳",
        "note": "2019年设立，跨境电商和沿边开放为特色。中老铁路通车后磨憨片区迎来新机遇，但整体规模偏小。"
    },
    "中国(黑龙江)自贸试验区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 4, "effectiveness": 3, "end_year": None,
        "momentum": "平稳",
        "note": "2019年设立，对俄贸易是唯一特色。黑河和绥芬河片区受中俄关系影响大，营商环境改善空间大。"
    },
    "中国(湖南)自贸试验区": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 5, "effectiveness": 5, "end_year": None,
        "momentum": "平稳",
        "note": "2020年设立，中非经贸合作和先进制造业为特色。中非经贸博览会永久落户长沙，工程机械出口全国第一。"
    },
    "中国(安徽)自贸试验区": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 7, "effectiveness": 7, "end_year": None,
        "momentum": "加速",
        "note": "2020年设立，合肥科创+量子+新能源汽车产业集群爆发式增长。科技创新策源地定位准确，发展势头强劲。"
    },
    "中国(北京)自贸试验区": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 7, "effectiveness": 6, "end_year": None,
        "momentum": "加速",
        "note": "2020年设立，服务业和数字经济为核心。全国首个以服务贸易为主的自贸区，数据跨境流动先行先试。"
    },
    "中国(新疆)自贸试验区": {
        "stage": "启动期", "stage_en": "Launch",
        "intensity": 6, "effectiveness": 3, "end_year": None,
        "momentum": "加速",
        "note": "2023年刚设立，全国最新自贸区。乌鲁木齐+喀什+霍尔果斯三片区，面向中亚开放。处于机构组建和制度设计阶段，实质成效待观察。"
    },

    # ==================== 基础设施超级工程 ====================
    "南水北调工程": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 6, "effectiveness": 7, "end_year": None,
        "momentum": "平稳",
        "note": "2002年启动，东中线已通水运行。累计调水超600亿立方米，北京地下水位显著回升。西线工程仍在论证中。"
    },
    "西气东输工程": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 5, "effectiveness": 8, "end_year": None,
        "momentum": "平稳",
        "note": "2000年启动，三线已建成投运。年输气量超1000亿立方米，彻底改变了中国能源版图。已进入常态化运营。"
    },
    "西电东送工程": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 7, "effectiveness": 8, "end_year": None,
        "momentum": "加速",
        "note": "2000年启动，特高压网络持续扩展。新能源大基地+特高压外送是新增长点，'沙戈荒'清洁能源基地建设推动第二轮扩张。"
    },
    "八纵八横高铁网": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 8, "effectiveness": 9, "end_year": 2035,
        "momentum": "平稳",
        "note": "2016年规划，目标4.5万公里。截至2024年底已建成4.5万公里基本成网，但部分西部线路仍在建设。运营效率全球最高，但部分线路客座率偏低。"
    },
    "川藏铁路": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 8, "effectiveness": 4, "end_year": 2035,
        "momentum": "平稳",
        "note": "2020年全线开工，总投资3198亿。世界最难铁路工程，需穿越14座高山21条大河。预计2035年左右建成，施工进展符合预期。"
    },
    "东数西算工程": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 7, "effectiveness": 6, "end_year": None,
        "momentum": "加速",
        "note": "2022年启动，8大算力枢纽10大数据中心集群。AI大模型爆发加速算力需求，西部数据中心上架率快速提升。"
    },
    "全国一体化大数据中心": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 6, "effectiveness": 5, "end_year": None,
        "momentum": "加速",
        "note": "2021年启动，与东数西算协同推进。数据要素市场化改革配套，但跨区域数据流通机制仍待完善。"
    },
    "新型基础设施建设(新基建)": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 7, "effectiveness": 7, "end_year": None,
        "momentum": "平稳",
        "note": "2020年提出，5G基站超400万个覆盖全球第一。概念已从热潮进入常态化，各领域按部门独立推进。AI算力基建成为当前重点。"
    },
    "国家水网工程": {
        "stage": "启动期", "stage_en": "Launch",
        "intensity": 7, "effectiveness": 3, "end_year": 2035,
        "momentum": "加速",
        "note": "2023年规划纲要印发，总投资预计超万亿。南水北调后续工程+国家骨干水网构建。处于规划设计和重点项目开工阶段。"
    },

    # ==================== 产业战略 ====================
    "中国制造2025": {
        "stage": "调整期", "stage_en": "Adjustment",
        "intensity": 8, "effectiveness": 7, "end_year": 2025,
        "momentum": "平稳",
        "note": "2015年发布，因中美贸易摩擦后官方不再高调提及但实质推进未停。十大领域中新能源汽车、5G等已实现突破，芯片和航空发动机仍为短板。2025年到期，将与新的制造业规划衔接。"
    },
    "双碳战略(碳达峰碳中和)": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 8, "effectiveness": 7, "end_year": 2060,
        "momentum": "加速",
        "note": "2020年提出，新能源装机量全球第一(风+光超12亿千瓦)。碳市场扩容、绿色金融蓬勃发展。但煤炭消费峰值尚未确认，碳达峰路径存不确定性。"
    },
    "新能源汽车产业发展规划": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 7, "effectiveness": 10, "end_year": 2035,
        "momentum": "平稳",
        "note": "2020年规划发布时目标2025年渗透率20%，实际2024年已超50%大幅超额完成。中国新能源汽车产销量全球第一，比亚迪、宁德时代成为世界级企业。已从政策驱动转向市场驱动。"
    },
    "乡村振兴战略": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 7, "effectiveness": 5, "end_year": 2035,
        "momentum": "平稳",
        "note": "2017年提出，2021年脱贫攻坚完成后转入全面推进。农业现代化进展但农村人口持续外流，城乡差距缩小速度慢于预期。种业振兴和农村基建为当前重点。"
    },
    "健康中国2030": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 7, "effectiveness": 6, "end_year": 2030,
        "momentum": "平稳",
        "note": "2016年发布，医保改革+创新药审批加速+DRG付费改革多线推进。疫情后公共卫生体系投入大增，但医疗资源区域不均衡仍突出。"
    },
    "数字中国建设": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 8, "effectiveness": 6, "end_year": None,
        "momentum": "加速",
        "note": "2023年中央发布总体布局规划，数字政府+数据要素市场化+信创替代三线并进。数据局成立标志制度化，但数据确权和跨境流通规则仍在探索。"
    },
    "国内国际双循环": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 6, "effectiveness": 5, "end_year": None,
        "momentum": "平稳",
        "note": "2020年提出，内需消费恢复不及预期。出口韧性超预期反而强化了外循环。政策框架清晰但消费提振效果有限，房地产拖累影响居民信心。"
    },
    "共同富裕示范区(浙江)": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 5, "effectiveness": 4, "end_year": None,
        "momentum": "减速",
        "note": "2021年提出后引发市场对'三次分配'和监管强化的担忧。浙江试点稳步推进但全国推广节奏放缓，政策表述趋于温和。"
    },

    # ==================== 科技创新战略 ====================
    "科技自立自强/举国体制": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 9, "effectiveness": 6, "end_year": None,
        "momentum": "加速",
        "note": "2020年提出后持续加码，大基金三期3440亿成立。芯片制造仍受限于美国出口管制(EUV光刻机)，但成熟制程自给率快速提升。举国体制效率与市场化创新的平衡是核心挑战。"
    },
    "人工智能发展规划": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 9, "effectiveness": 8, "end_year": 2030,
        "momentum": "加速",
        "note": "2017年发布，DeepSeek等大模型崛起标志中国AI实力。智算中心大规模建设，AI应用(自动驾驶、工业AI)快速落地。处于全球竞争最激烈的阶段。"
    },
    "量子科技发展战略": {
        "stage": "启动期", "stage_en": "Launch",
        "intensity": 7, "effectiveness": 5, "end_year": None,
        "momentum": "加速",
        "note": "2020年政治局集体学习后上升为国家战略。量子通信(京沪干线)领先全球，量子计算追赶IBM/Google。产业化仍处早期，国盾量子等企业规模尚小。"
    },
    "北斗卫星导航系统": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 6, "effectiveness": 9, "end_year": None,
        "momentum": "平稳",
        "note": "2020年全球组网完成，55颗卫星在轨运行。民用推广迅速，智能手机/汽车/农业/测绘广泛应用。已从建设期转入应用推广期，全球用户超15亿。"
    },
    "商业航天战略": {
        "stage": "启动期", "stage_en": "Launch",
        "intensity": 7, "effectiveness": 5, "end_year": None,
        "momentum": "加速",
        "note": "2024年政府工作报告首次提及商业航天。蓝箭、星际荣耀等民企崛起，卫星互联网(G60星链)开始部署。对标SpaceX但差距明显，处于产业爆发前夜。"
    },
    "低空经济": {
        "stage": "启动期", "stage_en": "Launch",
        "intensity": 8, "effectiveness": 3, "end_year": None,
        "momentum": "加速",
        "note": "2024年写入政府工作报告，各地竞相出台政策。eVTOL适航取证进行中，无人机物流试点扩大。空域管理改革是关键瓶颈，产业化需要3-5年。"
    },

    # ==================== 民生与社会战略 ====================
    "新型城镇化战略": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 6, "effectiveness": 7, "end_year": None,
        "momentum": "平稳",
        "note": "2014年规划发布，城镇化率从54%升至66%+。户籍改革逐步推进，城市群框架基本形成。但城镇化速度放缓，未来增量空间收窄。"
    },
    "三孩政策与人口战略": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 6, "effectiveness": 2, "end_year": None,
        "momentum": "减速",
        "note": "2021年放开三孩，配套托育/生育补贴政策密集出台。但生育率持续下降(2024年约0.98)，政策效果极不理想。已从鼓励生育转向适应老龄化的思路调整。"
    },
    "教育双减政策": {
        "stage": "成熟期", "stage_en": "Maturity",
        "intensity": 8, "effectiveness": 6, "end_year": None,
        "momentum": "平稳",
        "note": "2021年实施，K12学科培训行业基本出清(新东方等转型)。校外培训规模缩减80%+，但家长焦虑转向私教/游学等灰色地带。制度框架已稳定。"
    },
    "房住不炒与保障性住房": {
        "stage": "调整期", "stage_en": "Adjustment",
        "intensity": 8, "effectiveness": 5, "end_year": None,
        "momentum": "加速",
        "note": "2016年提出'房住不炒'，2024年后政策转向稳市场。限购限贷大面积放松，保障性住房和城中村改造成为新重点。从抑制需求转向供给侧改革。"
    },

    # ==================== 安全与治理战略 ====================
    "粮食安全战略": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 8, "effectiveness": 7, "end_year": None,
        "momentum": "加速",
        "note": "粮食产量连年超1.3万亿斤，但大豆对外依存度仍超80%。转基因种子商业化2024年正式放开，种业振兴进入实质阶段。耕地红线18亿亩守住但质量待提升。"
    },
    "能源安全战略": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 8, "effectiveness": 7, "end_year": None,
        "momentum": "加速",
        "note": "油气增储上产效果显著，原油产量重回2亿吨。核电重启批量化建设(每年6-10台)，新能源装机全球第一。能源结构转型加速但仍以煤为主。"
    },
    "国防和军队现代化": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 9, "effectiveness": 7, "end_year": 2027,
        "momentum": "加速",
        "note": "军费连续增长(2024年1.67万亿)，装备现代化加速(055驱逐舰、歼-20、福建舰)。2027年建军百年目标驱动，信息化智能化转型深入推进。"
    },
    "网络强国与数据安全": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 7, "effectiveness": 6, "end_year": None,
        "momentum": "加速",
        "note": "《数据安全法》《个保法》已实施，数据出境安全评估常态化。网络安全产业规模超2000亿，但企业合规成本高，部分外企因数据本地化要求调整中国战略。"
    },
    "西部大开发(新时代)": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 6, "effectiveness": 5, "end_year": None,
        "momentum": "平稳",
        "note": "2020年新时代西部大开发意见出台。风光大基地+东数西算为新抓手，但西部人口持续东流趋势未改。生态保护优先的定位限制了传统工业发展。"
    },
    "东北全面振兴": {
        "stage": "验证期", "stage_en": "Validation",
        "intensity": 6, "effectiveness": 3, "end_year": None,
        "momentum": "平稳",
        "note": "2023年中央再度发文推动东北振兴，但此轮已是第四轮振兴政策。人口外流、营商环境、国企改革三大痼疾未解。政策边际效果持续递减。"
    },
    "中部地区崛起": {
        "stage": "扩张期", "stage_en": "Expansion",
        "intensity": 7, "effectiveness": 7, "end_year": None,
        "momentum": "加速",
        "note": "2024年中央再度出台新时代中部崛起意见。武汉光谷、合肥新能源、长沙工程机械三大产业集群全国领先。中部六省GDP增速持续高于全国平均。"
    },
}


def apply_lifecycle_assessments():
    migrate_lifecycle_fields()
    conn = get_connection()
    cursor = conn.cursor()
    updated = 0

    for policy_name, assessment in LIFECYCLE_ASSESSMENTS.items():
        cursor.execute("""
            UPDATE policies SET
                lifecycle_stage = ?,
                lifecycle_stage_en = ?,
                execution_intensity = ?,
                execution_effectiveness = ?,
                expected_end_year = ?,
                lifecycle_note = ?,
                policy_momentum = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE name = ?
        """, (
            assessment["stage"],
            assessment["stage_en"],
            assessment["intensity"],
            assessment["effectiveness"],
            assessment.get("end_year"),
            assessment["note"],
            assessment["momentum"],
            policy_name,
        ))
        if cursor.rowcount > 0:
            updated += 1

    conn.commit()
    conn.close()
    print(f"Updated lifecycle data for {updated} policies")


if __name__ == "__main__":
    apply_lifecycle_assessments()
