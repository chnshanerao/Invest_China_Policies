import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection, init_db


CATEGORIES = [
    {"name": "国际战略", "name_en": "International Strategy", "description": "跨国合作与国际经济布局", "sort_order": 1},
    {"name": "区域重大战略", "name_en": "Regional Mega-Strategy", "description": "跨省级区域协调发展战略", "sort_order": 2},
    {"name": "经济特区", "name_en": "Special Economic Zone", "description": "享有特殊经济政策的区域", "sort_order": 3},
    {"name": "国家级新区", "name_en": "National New Area", "description": "国务院批复设立的新区", "sort_order": 4},
    {"name": "自贸试验区/港", "name_en": "Free Trade Zone/Port", "description": "自由贸易试验区和自由贸易港", "sort_order": 5},
    {"name": "基础设施超级工程", "name_en": "Infrastructure Mega-Project", "description": "国家级重大基础设施项目", "sort_order": 6},
    {"name": "产业战略", "name_en": "Industrial Strategy", "description": "国家级产业发展战略", "sort_order": 7},
    {"name": "科技创新战略", "name_en": "Tech & Innovation", "description": "科技自主创新与数字化战略", "sort_order": 8},
    {"name": "民生与社会战略", "name_en": "Social Strategy", "description": "民生保障与社会发展", "sort_order": 9},
    {"name": "安全与治理战略", "name_en": "Security & Governance", "description": "国家安全与治理体系", "sort_order": 10},
]


POLICIES = [
    # === 国际战略 ===
    {"name": "一带一路", "name_en": "Belt and Road Initiative", "category": "国际战略", "year": 2013,
     "region": "全球", "description": "丝绸之路经济带和21世纪海上丝绸之路", "key_goals": "促进国际合作,基础设施互联互通,贸易畅通",
     "total_investment": 10000, "risk": "高",
     "opportunities": [
         {"sector": "基建", "title": "海外基建工程承包", "type": "行业", "desc": "中国交建、中国中铁等央企海外项目", "instruments": "601800.SH,601390.SH", "etfs": "159819", "risk": "高", "return": "中", "horizon": "长期"},
         {"sector": "港口物流", "title": "港口与物流网络", "type": "主题", "desc": "沿线港口投资运营,如招商港口、中远海控", "instruments": "001872.SZ,601919.SH", "etfs": "159869", "risk": "中", "return": "中", "horizon": "中期"},
         {"sector": "金融", "title": "人民币国际化", "type": "趋势", "desc": "跨境支付、数字货币、离岸人民币业务", "instruments": "601988.SH,601398.SH", "risk": "中", "return": "中", "horizon": "长期"},
     ]},
    {"name": "RCEP区域全面经济伙伴关系", "name_en": "RCEP", "category": "国际战略", "year": 2022,
     "region": "亚太15国", "description": "全球最大自由贸易协定", "key_goals": "降低关税,开放市场,统一规则",
     "risk": "中",
     "opportunities": [
         {"sector": "外贸", "title": "对RCEP国家出口增长", "type": "趋势", "desc": "纺织服装、电子、机械出口受益", "instruments": "600690.SH,002241.SZ", "risk": "中", "return": "中", "horizon": "中期"},
         {"sector": "跨境电商", "title": "跨境电商平台", "type": "行业", "desc": "Temu、Shein等平台东南亚扩张", "instruments": "PDD,BABA", "risk": "中", "return": "高", "horizon": "中期"},
     ]},
    {"name": "中国-东盟自贸区升级", "name_en": "China-ASEAN FTA 3.0", "category": "国际战略", "year": 2024,
     "region": "东盟", "description": "中国-东盟自贸区3.0版升级谈判", "key_goals": "数字经济,绿色经济,供应链合作",
     "risk": "中",
     "opportunities": [
         {"sector": "数字经济", "title": "东南亚数字基础设施", "type": "行业", "desc": "数据中心、云服务、数字支付出海", "instruments": "BABA,PDD", "risk": "中", "return": "高", "horizon": "中期"},
     ]},

    # === 区域重大战略 ===
    {"name": "京津冀协同发展", "name_en": "Beijing-Tianjin-Hebei Integration", "category": "区域重大战略", "year": 2014,
     "region": "京津冀", "description": "疏解北京非首都功能,协同发展", "key_goals": "产业转移,交通一体化,生态协同",
     "total_investment": 15000, "risk": "中",
     "opportunities": [
         {"sector": "交通", "title": "京津冀城际铁路网", "type": "基建", "desc": "城际铁路、高速公路互联互通", "instruments": "601006.SH,600548.SH", "risk": "低", "return": "中", "horizon": "中期"},
         {"sector": "地产", "title": "环京产业园区", "type": "地产", "desc": "廊坊、保定等地产业园区发展", "instruments": "600340.SH", "risk": "高", "return": "中", "horizon": "长期"},
     ]},
    {"name": "雄安新区", "name_en": "Xiongan New Area", "category": "区域重大战略", "year": 2017,
     "region": "河北雄安", "description": "千年大计,疏解北京非首都功能集中承载地", "key_goals": "智慧城市,绿色低碳,创新驱动",
     "total_investment": 10000, "gdp": 68.9, "fiscal_revenue": 3.08, "debt": 280.4, "risk": "高",
     "opportunities": [
         {"sector": "智慧城市", "title": "雄安智慧基建", "type": "主题", "desc": "数字孪生城市、BIM、物联网基建", "instruments": "002312.SZ,300098.SZ", "risk": "高", "return": "低", "horizon": "长期"},
         {"sector": "建筑", "title": "雄安建设工程", "type": "基建", "desc": "中国建筑等央企雄安项目", "instruments": "601668.SH", "risk": "中", "return": "低", "horizon": "中期"},
     ]},
    {"name": "长江经济带发展", "name_en": "Yangtze River Economic Belt", "category": "区域重大战略", "year": 2014,
     "region": "长江沿线11省市", "description": "共抓大保护、不搞大开发", "key_goals": "生态优先,绿色发展,产业转型升级",
     "total_investment": 20000, "risk": "中",
     "opportunities": [
         {"sector": "环保", "title": "长江生态修复", "type": "行业", "desc": "水治理、污染防治、生态修复", "instruments": "600388.SH,300070.SZ", "risk": "中", "return": "中", "horizon": "中期"},
         {"sector": "航运", "title": "长江航运升级", "type": "基建", "desc": "长江航道整治、港口升级", "instruments": "600717.SH,600279.SH", "risk": "低", "return": "中", "horizon": "中期"},
     ]},
    {"name": "粤港澳大湾区", "name_en": "Greater Bay Area", "category": "区域重大战略", "year": 2019,
     "region": "粤港澳", "description": "建设世界级城市群和国际一流湾区", "key_goals": "科技创新,金融开放,互联互通",
     "total_investment": 15000, "risk": "中",
     "opportunities": [
         {"sector": "科技", "title": "大湾区科创中心", "type": "行业", "desc": "深圳-香港科技走廊,生物医药,AI", "instruments": "000725.SZ,300760.SZ", "etfs": "159984", "risk": "中", "return": "高", "horizon": "中期"},
         {"sector": "金融", "title": "跨境金融互联互通", "type": "趋势", "desc": "跨境理财通、保险通、债券通", "instruments": "600030.SH,601688.SH", "risk": "中", "return": "中", "horizon": "中期"},
         {"sector": "基建", "title": "大湾区交通基建", "type": "基建", "desc": "深中通道、港珠澳大桥、城际铁路", "instruments": "600548.SH", "risk": "低", "return": "中", "horizon": "中期"},
     ]},
    {"name": "长三角一体化发展", "name_en": "Yangtze Delta Integration", "category": "区域重大战略", "year": 2018,
     "region": "沪苏浙皖", "description": "高质量一体化发展示范区", "key_goals": "产业协同,科技创新,基础设施互联",
     "total_investment": 18000, "risk": "低",
     "opportunities": [
         {"sector": "半导体", "title": "长三角集成电路产业集群", "type": "行业", "desc": "上海+无锡+合肥芯片产业链", "instruments": "688981.SH,002371.SZ", "etfs": "512480", "risk": "中", "return": "高", "horizon": "长期"},
         {"sector": "新能源", "title": "长三角新能源汽车产业链", "type": "行业", "desc": "特斯拉上海+蔚来合肥+理想常州", "instruments": "NIO,LI,XPEV", "risk": "中", "return": "高", "horizon": "中期"},
     ]},
    {"name": "黄河流域生态保护和高质量发展", "name_en": "Yellow River Ecological Protection", "category": "区域重大战略", "year": 2019,
     "region": "黄河沿线9省区", "description": "生态保护,水资源节约集约利用", "key_goals": "生态保护,水安全,文化传承",
     "risk": "中",
     "opportunities": [
         {"sector": "水利", "title": "黄河水利工程", "type": "基建", "desc": "水利枢纽、灌区改造、节水工程", "instruments": "600502.SH,002532.SZ", "risk": "低", "return": "中", "horizon": "长期"},
     ]},
    {"name": "成渝地区双城经济圈", "name_en": "Chengdu-Chongqing Economic Circle", "category": "区域重大战略", "year": 2020,
     "region": "川渝", "description": "打造中国经济第四极", "key_goals": "西部大开发,产业升级,内陆开放",
     "risk": "中",
     "opportunities": [
         {"sector": "消费", "title": "成渝消费升级", "type": "趋势", "desc": "西部新一线城市消费扩张", "instruments": "000568.SZ,600887.SH", "risk": "低", "return": "中", "horizon": "中期"},
         {"sector": "电子", "title": "成渝电子信息产业", "type": "行业", "desc": "笔电、芯片封测、智能终端产业集群", "instruments": "000725.SZ", "risk": "中", "return": "中", "horizon": "中期"},
     ]},

    # === 经济特区 ===
    {"name": "深圳经济特区", "name_en": "Shenzhen SEZ", "category": "经济特区", "year": 1980,
     "region": "广东深圳", "description": "中国改革开放窗口", "key_goals": "中国特色社会主义先行示范区",
     "gdp": 36802, "risk": "低",
     "opportunities": [
         {"sector": "科技", "title": "深圳高新技术产业", "type": "行业", "desc": "华为、腾讯、比亚迪等龙头企业生态", "instruments": "700.HK,002594.SZ,300750.SZ", "risk": "中", "return": "高", "horizon": "长期"},
     ]},
    {"name": "珠海经济特区", "name_en": "Zhuhai SEZ", "category": "经济特区", "year": 1980,
     "region": "广东珠海", "description": "港珠澳大桥西端", "key_goals": "粤港澳合作,横琴开发",
     "risk": "中",
     "opportunities": [
         {"sector": "旅游", "title": "珠海-横琴文旅", "type": "行业", "desc": "长隆、横琴旅游岛", "instruments": "", "risk": "中", "return": "中", "horizon": "中期"},
     ]},
    {"name": "汕头经济特区", "name_en": "Shantou SEZ", "category": "经济特区", "year": 1980,
     "region": "广东汕头", "description": "侨乡经济特区", "key_goals": "华侨经济,对外开放",
     "risk": "中", "opportunities": []},
    {"name": "厦门经济特区", "name_en": "Xiamen SEZ", "category": "经济特区", "year": 1980,
     "region": "福建厦门", "description": "对台经贸窗口", "key_goals": "两岸交流,海上丝绸之路",
     "risk": "低", "opportunities": []},
    {"name": "海南经济特区", "name_en": "Hainan SEZ", "category": "经济特区", "year": 1988,
     "region": "海南", "description": "中国最大经济特区", "key_goals": "自贸港建设,国际旅游岛",
     "risk": "中", "opportunities": []},
    {"name": "喀什经济特区", "name_en": "Kashgar SEZ", "category": "经济特区", "year": 2010,
     "region": "新疆喀什", "description": "面向中亚南亚的开放窗口", "key_goals": "边境贸易,对外开放",
     "risk": "高", "opportunities": []},
    {"name": "霍尔果斯经济特区", "name_en": "Horgos SEZ", "category": "经济特区", "year": 2010,
     "region": "新疆霍尔果斯", "description": "中哈边境口岸城市", "key_goals": "口岸经济,跨境贸易",
     "risk": "高", "opportunities": []},

    # === 国家级新区 ===
    {"name": "上海浦东新区", "name_en": "Shanghai Pudong", "category": "国家级新区", "year": 1992,
     "region": "上海", "description": "中国改革开放地标", "key_goals": "引领区建设,国际金融中心",
     "gdp": 18008, "risk": "低",
     "opportunities": [
         {"sector": "金融", "title": "浦东金融创新", "type": "行业", "desc": "上海证交所、期货、保险创新", "instruments": "601788.SH,600030.SH", "risk": "低", "return": "中", "horizon": "中期"},
         {"sector": "生物医药", "title": "张江生物医药", "type": "行业", "desc": "张江药谷,创新药研发", "instruments": "688180.SH,688185.SH", "etfs": "515120", "risk": "中", "return": "高", "horizon": "长期"},
     ]},
    {"name": "天津滨海新区", "name_en": "Tianjin Binhai", "category": "国家级新区", "year": 2006,
     "region": "天津", "description": "北方经济中心", "key_goals": "先进制造,港口经济",
     "risk": "中", "opportunities": []},
    {"name": "重庆两江新区", "name_en": "Chongqing Liangjiang", "category": "国家级新区", "year": 2010,
     "region": "重庆", "description": "内陆首个国家级新区", "key_goals": "内陆开放,智能制造",
     "risk": "中", "opportunities": []},
    {"name": "浙江舟山群岛新区", "name_en": "Zhoushan Archipelago", "category": "国家级新区", "year": 2011,
     "region": "浙江舟山", "description": "海洋经济示范区", "key_goals": "大宗商品储运,海洋经济",
     "risk": "中", "opportunities": []},
    {"name": "甘肃兰州新区", "name_en": "Lanzhou New Area", "category": "国家级新区", "year": 2012,
     "region": "甘肃兰州", "description": "西北重要增长极", "key_goals": "西北开发,产业承接",
     "risk": "高", "opportunities": []},
    {"name": "广东南沙新区", "name_en": "Guangzhou Nansha", "category": "国家级新区", "year": 2012,
     "region": "广东广州", "description": "粤港澳全面合作示范区", "key_goals": "粤港澳合作,航运物流",
     "risk": "中", "opportunities": []},
    {"name": "陕西西咸新区", "name_en": "Xixian New Area", "category": "国家级新区", "year": 2014,
     "region": "陕西", "description": "创新城市发展方式", "key_goals": "西安-咸阳一体化",
     "risk": "中", "opportunities": []},
    {"name": "贵州贵安新区", "name_en": "Gui'an New Area", "category": "国家级新区", "year": 2014,
     "region": "贵州", "description": "西部大数据中心", "key_goals": "大数据,绿色经济",
     "risk": "中",
     "opportunities": [
         {"sector": "数据中心", "title": "贵安大数据产业", "type": "行业", "desc": "苹果、华为、腾讯数据中心集群", "instruments": "603881.SH", "risk": "中", "return": "中", "horizon": "中期"},
     ]},
    {"name": "青岛西海岸新区", "name_en": "Qingdao West Coast", "category": "国家级新区", "year": 2014,
     "region": "山东青岛", "description": "海洋经济新区", "key_goals": "海洋科技,影视文化",
     "risk": "低", "opportunities": []},
    {"name": "大连金普新区", "name_en": "Dalian Jinpu", "category": "国家级新区", "year": 2014,
     "region": "辽宁大连", "description": "东北振兴龙头", "key_goals": "先进装备制造,东北亚合作",
     "risk": "中", "opportunities": []},
    {"name": "四川天府新区", "name_en": "Sichuan Tianfu", "category": "国家级新区", "year": 2014,
     "region": "四川成都", "description": "西部地区核心增长极", "key_goals": "公园城市,科技创新",
     "risk": "低", "opportunities": []},
    {"name": "湖南湘江新区", "name_en": "Xiangjiang New Area", "category": "国家级新区", "year": 2015,
     "region": "湖南长沙", "description": "中部崛起战略支点", "key_goals": "高端制造,科技创新",
     "risk": "低", "opportunities": []},
    {"name": "南京江北新区", "name_en": "Nanjing Jiangbei", "category": "国家级新区", "year": 2015,
     "region": "江苏南京", "description": "自主创新先导区", "key_goals": "集成电路,生命健康",
     "risk": "低",
     "opportunities": [
         {"sector": "芯片", "title": "江北新区芯片产业", "type": "行业", "desc": "台积电南京、ASML等集聚", "instruments": "688981.SH", "risk": "中", "return": "高", "horizon": "长期"},
     ]},
    {"name": "福州新区", "name_en": "Fuzhou New Area", "category": "国家级新区", "year": 2015,
     "region": "福建福州", "description": "海上丝绸之路战略枢纽", "key_goals": "两岸合作,海洋经济",
     "risk": "中", "opportunities": []},
    {"name": "云南滇中新区", "name_en": "Yunnan Dianzhong", "category": "国家级新区", "year": 2015,
     "region": "云南昆明", "description": "面向南亚东南亚辐射中心", "key_goals": "沿边开放,跨境合作",
     "risk": "中", "opportunities": []},
    {"name": "哈尔滨新区", "name_en": "Harbin New Area", "category": "国家级新区", "year": 2015,
     "region": "黑龙江哈尔滨", "description": "对俄合作中心", "key_goals": "对俄合作,老工业基地振兴",
     "risk": "高", "opportunities": []},
    {"name": "长春新区", "name_en": "Changchun New Area", "category": "国家级新区", "year": 2016,
     "region": "吉林长春", "description": "东北振兴创新中心", "key_goals": "汽车产业升级,光电信息",
     "risk": "中", "opportunities": []},
    {"name": "江西赣江新区", "name_en": "Ganjiang New Area", "category": "国家级新区", "year": 2016,
     "region": "江西南昌", "description": "中部地区崛起", "key_goals": "绿色金融,新能源",
     "risk": "中", "opportunities": []},
    {"name": "河北雄安新区", "name_en": "Hebei Xiongan", "category": "国家级新区", "year": 2017,
     "region": "河北", "description": "千年大计(与区域战略中雄安新区为同一政策)", "key_goals": "疏解北京非首都功能",
     "risk": "高", "opportunities": []},

    # === 自贸试验区/港 ===
    {"name": "中国(上海)自贸试验区", "name_en": "Shanghai FTZ", "category": "自贸试验区/港", "year": 2013,
     "region": "上海", "description": "中国第一个自贸试验区", "key_goals": "制度创新,金融开放,贸易便利化",
     "risk": "低",
     "opportunities": [
         {"sector": "金融", "title": "上海自贸金融创新", "type": "行业", "desc": "跨境投融资、离岸金融、金融科技", "instruments": "601688.SH,600030.SH", "risk": "低", "return": "中", "horizon": "中期"},
     ]},
    {"name": "中国(广东)自贸试验区", "name_en": "Guangdong FTZ", "category": "自贸试验区/港", "year": 2015,
     "region": "广东", "description": "粤港澳深度合作示范区", "key_goals": "粤港澳合作,服务贸易",
     "risk": "低", "opportunities": []},
    {"name": "中国(天津)自贸试验区", "name_en": "Tianjin FTZ", "category": "自贸试验区/港", "year": 2015,
     "region": "天津", "description": "京津冀协同发展示范", "key_goals": "融资租赁,平行进口",
     "risk": "中", "opportunities": []},
    {"name": "中国(福建)自贸试验区", "name_en": "Fujian FTZ", "category": "自贸试验区/港", "year": 2015,
     "region": "福建", "description": "对台自贸合作", "key_goals": "两岸经贸,海上丝绸之路",
     "risk": "中", "opportunities": []},
    {"name": "中国(辽宁)自贸试验区", "name_en": "Liaoning FTZ", "category": "自贸试验区/港", "year": 2017,
     "region": "辽宁", "description": "东北振兴制度创新", "key_goals": "国企改革,东北亚合作",
     "risk": "中", "opportunities": []},
    {"name": "中国(浙江)自贸试验区", "name_en": "Zhejiang FTZ", "category": "自贸试验区/港", "year": 2017,
     "region": "浙江", "description": "大宗商品贸易自由化", "key_goals": "油气全产业链,数字贸易",
     "risk": "低",
     "opportunities": [
         {"sector": "大宗商品", "title": "舟山油气交易中心", "type": "行业", "desc": "原油、LNG贸易枢纽", "instruments": "600688.SH", "risk": "中", "return": "中", "horizon": "中期"},
     ]},
    {"name": "中国(河南)自贸试验区", "name_en": "Henan FTZ", "category": "自贸试验区/港", "year": 2017,
     "region": "河南", "description": "中部物流枢纽", "key_goals": "物流枢纽,跨境电商",
     "risk": "中", "opportunities": []},
    {"name": "中国(湖北)自贸试验区", "name_en": "Hubei FTZ", "category": "自贸试验区/港", "year": 2017,
     "region": "湖北", "description": "长江经济带创新驱动", "key_goals": "光电信息,生物医药",
     "risk": "中", "opportunities": []},
    {"name": "中国(重庆)自贸试验区", "name_en": "Chongqing FTZ", "category": "自贸试验区/港", "year": 2017,
     "region": "重庆", "description": "西部大开发重要支点", "key_goals": "内陆开放,中新互联互通",
     "risk": "中", "opportunities": []},
    {"name": "中国(四川)自贸试验区", "name_en": "Sichuan FTZ", "category": "自贸试验区/港", "year": 2017,
     "region": "四川", "description": "西部门户枢纽", "key_goals": "航空经济,服务贸易",
     "risk": "中", "opportunities": []},
    {"name": "中国(陕西)自贸试验区", "name_en": "Shaanxi FTZ", "category": "自贸试验区/港", "year": 2017,
     "region": "陕西", "description": "一带一路核心区", "key_goals": "人文交流,能源化工",
     "risk": "中", "opportunities": []},
    {"name": "中国(海南)自贸港", "name_en": "Hainan FTP", "category": "自贸试验区/港", "year": 2018,
     "region": "海南", "description": "中国唯一自由贸易港,2025年封关", "key_goals": "零关税,低税率,自由便利",
     "total_investment": 4000, "gdp": 810.9, "fiscal_revenue": 90.37, "risk": "中",
     "opportunities": [
         {"sector": "免税消费", "title": "海南离岛免税", "type": "行业", "desc": "中国中免为核心,免税消费持续增长", "instruments": "601888.SH,601838.SH", "etfs": "", "risk": "中", "return": "高", "horizon": "中期"},
         {"sector": "旅游", "title": "国际旅游消费中心", "type": "趋势", "desc": "入境旅游、医疗旅游、邮轮经济", "instruments": "000069.SZ,600138.SH", "risk": "中", "return": "中", "horizon": "中期"},
         {"sector": "贸易", "title": "跨境贸易与加工", "type": "行业", "desc": "加工增值30%免关税政策受益产业", "instruments": "", "risk": "中", "return": "中", "horizon": "中期"},
     ]},
    {"name": "中国(山东)自贸试验区", "name_en": "Shandong FTZ", "category": "自贸试验区/港", "year": 2019,
     "region": "山东", "description": "海洋经济创新发展", "key_goals": "海洋经济,日韩合作",
     "risk": "中", "opportunities": []},
    {"name": "中国(江苏)自贸试验区", "name_en": "Jiangsu FTZ", "category": "自贸试验区/港", "year": 2019,
     "region": "江苏", "description": "开放型经济高质量发展", "key_goals": "先进制造,生物医药",
     "risk": "低", "opportunities": []},
    {"name": "中国(广西)自贸试验区", "name_en": "Guangxi FTZ", "category": "自贸试验区/港", "year": 2019,
     "region": "广西", "description": "面向东盟开放门户", "key_goals": "东盟合作,陆海新通道",
     "risk": "中", "opportunities": []},
    {"name": "中国(河北)自贸试验区", "name_en": "Hebei FTZ", "category": "自贸试验区/港", "year": 2019,
     "region": "河北", "description": "京津冀协同发展配套", "key_goals": "生物医药,数字贸易",
     "risk": "中", "opportunities": []},
    {"name": "中国(云南)自贸试验区", "name_en": "Yunnan FTZ", "category": "自贸试验区/港", "year": 2019,
     "region": "云南", "description": "沿边开放示范", "key_goals": "跨境贸易,GMS合作",
     "risk": "中", "opportunities": []},
    {"name": "中国(黑龙江)自贸试验区", "name_en": "Heilongjiang FTZ", "category": "自贸试验区/港", "year": 2019,
     "region": "黑龙江", "description": "对俄远东合作", "key_goals": "对俄贸易,粮食加工",
     "risk": "高", "opportunities": []},
    {"name": "中国(湖南)自贸试验区", "name_en": "Hunan FTZ", "category": "自贸试验区/港", "year": 2020,
     "region": "湖南", "description": "中非经贸合作", "key_goals": "先进制造,中非合作",
     "risk": "中", "opportunities": []},
    {"name": "中国(安徽)自贸试验区", "name_en": "Anhui FTZ", "category": "自贸试验区/港", "year": 2020,
     "region": "安徽", "description": "科技创新策源地", "key_goals": "量子科技,人工智能",
     "risk": "低",
     "opportunities": [
         {"sector": "量子科技", "title": "合肥量子计算产业", "type": "前沿", "desc": "国盾量子、本源量子等", "instruments": "688027.SH", "risk": "高", "return": "高", "horizon": "长期"},
     ]},
    {"name": "中国(北京)自贸试验区", "name_en": "Beijing FTZ", "category": "自贸试验区/港", "year": 2020,
     "region": "北京", "description": "服务业扩大开放", "key_goals": "数字经济,金融科技",
     "risk": "低", "opportunities": []},
    {"name": "中国(新疆)自贸试验区", "name_en": "Xinjiang FTZ", "category": "自贸试验区/港", "year": 2023,
     "region": "新疆", "description": "面向中亚开放", "key_goals": "中亚贸易,能源合作",
     "risk": "高", "opportunities": []},

    # === 基础设施超级工程 ===
    {"name": "南水北调工程", "name_en": "South-to-North Water Diversion", "category": "基础设施超级工程", "year": 2002,
     "region": "全国", "description": "世界最大调水工程", "key_goals": "解决北方水资源短缺",
     "total_investment": 5000, "risk": "低",
     "opportunities": [
         {"sector": "水务", "title": "北方水务运营", "type": "行业", "desc": "水务运营、水处理设备", "instruments": "600008.SH,300070.SZ", "risk": "低", "return": "中", "horizon": "长期"},
     ]},
    {"name": "西气东输工程", "name_en": "West-East Gas Pipeline", "category": "基础设施超级工程", "year": 2000,
     "region": "全国", "description": "天然气管道工程", "key_goals": "西部天然气送往东部",
     "total_investment": 3000, "risk": "低", "opportunities": []},
    {"name": "西电东送工程", "name_en": "West-East Electricity Transfer", "category": "基础设施超级工程", "year": 2000,
     "region": "全国", "description": "西部电力送往东部", "key_goals": "能源均衡配置",
     "total_investment": 5000, "risk": "低",
     "opportunities": [
         {"sector": "特高压", "title": "特高压输电网络", "type": "行业", "desc": "特高压设备与建设", "instruments": "600089.SH,300341.SZ", "etfs": "159811", "risk": "中", "return": "中", "horizon": "中期"},
     ]},
    {"name": "八纵八横高铁网", "name_en": "8+8 HSR Network", "category": "基础设施超级工程", "year": 2016,
     "region": "全国", "description": "国家高速铁路网规划", "key_goals": "4.5万公里高铁网络",
     "total_investment": 35000, "risk": "低",
     "opportunities": [
         {"sector": "铁路", "title": "高铁产业链", "type": "行业", "desc": "中国中车、铁路信号、轨道交通", "instruments": "601766.SH,688009.SH,003009.SZ", "risk": "低", "return": "中", "horizon": "长期"},
     ]},
    {"name": "川藏铁路", "name_en": "Sichuan-Tibet Railway", "category": "基础设施超级工程", "year": 2020,
     "region": "川藏", "description": "世界最难铁路工程", "key_goals": "西藏交通改善,国防安全",
     "total_investment": 3198, "risk": "中",
     "opportunities": [
         {"sector": "基建", "title": "川藏铁路建设", "type": "基建", "desc": "隧道掘进、桥梁建设、地质勘探", "instruments": "601186.SH,600170.SH", "risk": "中", "return": "中", "horizon": "中期"},
     ]},
    {"name": "东数西算工程", "name_en": "East Data West Computing", "category": "基础设施超级工程", "year": 2022,
     "region": "全国8大枢纽", "description": "算力基础设施国家布局", "key_goals": "8大算力枢纽,10大数据中心集群",
     "total_investment": 4000, "risk": "中",
     "opportunities": [
         {"sector": "算力", "title": "数据中心与算力", "type": "行业", "desc": "服务器、光模块、液冷散热", "instruments": "000977.SZ,002475.SZ,603019.SH", "etfs": "159513", "risk": "中", "return": "高", "horizon": "中期"},
     ]},
    {"name": "全国一体化大数据中心", "name_en": "National Integrated Data Center", "category": "基础设施超级工程", "year": 2021,
     "region": "全国", "description": "数据中心体系化布局", "key_goals": "算力资源协同,数据流通",
     "risk": "中", "opportunities": []},
    {"name": "新型基础设施建设(新基建)", "name_en": "New Infrastructure", "category": "基础设施超级工程", "year": 2020,
     "region": "全国", "description": "5G、人工智能、工业互联网等", "key_goals": "数字化转型基础设施",
     "total_investment": 10000, "risk": "中",
     "opportunities": [
         {"sector": "5G", "title": "5G网络与应用", "type": "行业", "desc": "基站设备、终端、应用", "instruments": "600941.SH,000063.SZ", "etfs": "515050", "risk": "中", "return": "中", "horizon": "中期"},
         {"sector": "AI基建", "title": "AI算力基础设施", "type": "前沿", "desc": "GPU服务器、AI芯片、智算中心", "instruments": "002230.SZ,688256.SH", "risk": "中", "return": "高", "horizon": "中期"},
     ]},
    {"name": "国家水网工程", "name_en": "National Water Network", "category": "基础设施超级工程", "year": 2023,
     "region": "全国", "description": "国家级水利基础设施网络", "key_goals": "水安全保障",
     "total_investment": 10000, "risk": "低",
     "opportunities": [
         {"sector": "水利", "title": "水利基建投资", "type": "基建", "desc": "水利枢纽、管网、智慧水务", "instruments": "600502.SH,300211.SZ", "risk": "低", "return": "中", "horizon": "长期"},
     ]},

    # === 产业战略 ===
    {"name": "中国制造2025", "name_en": "Made in China 2025", "category": "产业战略", "year": 2015,
     "region": "全国", "description": "制造业强国战略", "key_goals": "十大重点领域突破,自主可控",
     "risk": "中",
     "opportunities": [
         {"sector": "高端装备", "title": "高端装备国产替代", "type": "行业", "desc": "工业母机、机器人、航空发动机", "instruments": "688305.SH,300124.SZ", "etfs": "159667", "risk": "中", "return": "高", "horizon": "长期"},
         {"sector": "新材料", "title": "先进材料国产化", "type": "行业", "desc": "碳纤维、半导体材料、稀土永磁", "instruments": "300699.SZ,688981.SH", "risk": "中", "return": "高", "horizon": "长期"},
     ]},
    {"name": "双碳战略(碳达峰碳中和)", "name_en": "Dual Carbon Strategy", "category": "产业战略", "year": 2020,
     "region": "全国", "description": "2030碳达峰,2060碳中和", "key_goals": "新能源转型,节能减排",
     "risk": "中",
     "opportunities": [
         {"sector": "光伏", "title": "光伏产业链", "type": "行业", "desc": "硅料、电池、组件、逆变器", "instruments": "601012.SH,002459.SZ,300274.SZ", "etfs": "159857", "risk": "中", "return": "高", "horizon": "中期"},
         {"sector": "储能", "title": "储能产业", "type": "行业", "desc": "锂电储能、钠电池、抽蓄", "instruments": "300750.SZ,002074.SZ", "etfs": "159566", "risk": "中", "return": "高", "horizon": "中期"},
         {"sector": "碳交易", "title": "碳交易市场", "type": "趋势", "desc": "全国碳市场扩容", "instruments": "", "risk": "中", "return": "中", "horizon": "长期"},
         {"sector": "风电", "title": "风电产业链", "type": "行业", "desc": "海上风电、风机整机、叶片", "instruments": "601016.SH,002202.SZ", "etfs": "159819", "risk": "中", "return": "中", "horizon": "中期"},
     ]},
    {"name": "新能源汽车产业发展规划", "name_en": "NEV Industry Plan", "category": "产业战略", "year": 2020,
     "region": "全国", "description": "新能源汽车强国", "key_goals": "2025年新能源车渗透率20%以上(已超额完成)",
     "risk": "中",
     "opportunities": [
         {"sector": "整车", "title": "新能源整车", "type": "行业", "desc": "比亚迪、蔚来、理想、小鹏", "instruments": "002594.SZ,NIO,LI,XPEV", "etfs": "515030", "risk": "中", "return": "高", "horizon": "中期"},
         {"sector": "动力电池", "title": "动力电池产业链", "type": "行业", "desc": "宁德时代、亿纬锂能等", "instruments": "300750.SZ,300014.SZ", "risk": "中", "return": "高", "horizon": "中期"},
         {"sector": "充电桩", "title": "充电基础设施", "type": "基建", "desc": "充电桩建设与运营", "instruments": "300001.SZ,002121.SZ", "risk": "中", "return": "中", "horizon": "中期"},
     ]},
    {"name": "乡村振兴战略", "name_en": "Rural Revitalization", "category": "产业战略", "year": 2017,
     "region": "全国", "description": "全面推进乡村振兴", "key_goals": "农业现代化,农村建设,农民增收",
     "risk": "中",
     "opportunities": [
         {"sector": "农业", "title": "智慧农业与种业", "type": "行业", "desc": "种子、农机、数字农业", "instruments": "000998.SZ,601952.SH", "risk": "中", "return": "中", "horizon": "长期"},
     ]},
    {"name": "健康中国2030", "name_en": "Healthy China 2030", "category": "产业战略", "year": 2016,
     "region": "全国", "description": "建设健康中国", "key_goals": "医疗体系改革,全民健康",
     "risk": "低",
     "opportunities": [
         {"sector": "医药", "title": "创新药与医疗器械", "type": "行业", "desc": "创新药研发、高端医疗器械国产替代", "instruments": "688180.SH,300760.SZ,300003.SZ", "etfs": "515120", "risk": "中", "return": "高", "horizon": "长期"},
         {"sector": "医疗服务", "title": "互联网医疗与养老", "type": "趋势", "desc": "远程医疗、养老服务、健康管理", "instruments": "300347.SZ", "risk": "中", "return": "中", "horizon": "中期"},
     ]},
    {"name": "数字中国建设", "name_en": "Digital China", "category": "产业战略", "year": 2023,
     "region": "全国", "description": "全面数字化转型", "key_goals": "数字政府,数字经济,数字社会",
     "risk": "中",
     "opportunities": [
         {"sector": "信创", "title": "信创产业(国产替代)", "type": "行业", "desc": "国产操作系统、数据库、办公软件", "instruments": "688111.SH,300378.SZ,688588.SH", "risk": "中", "return": "高", "horizon": "中期"},
     ]},
    {"name": "国内国际双循环", "name_en": "Dual Circulation", "category": "产业战略", "year": 2020,
     "region": "全国", "description": "以国内大循环为主体", "key_goals": "扩大内需,促进消费,产业链安全",
     "risk": "中",
     "opportunities": [
         {"sector": "消费", "title": "内需消费升级", "type": "趋势", "desc": "国潮品牌、中产消费、服务消费", "instruments": "600887.SH,603605.SH", "risk": "低", "return": "中", "horizon": "中期"},
     ]},
    {"name": "共同富裕示范区(浙江)", "name_en": "Common Prosperity Demo Zone", "category": "产业战略", "year": 2021,
     "region": "浙江", "description": "共同富裕先行先试", "key_goals": "缩小贫富差距,第三次分配",
     "risk": "中", "opportunities": []},

    # === 科技创新战略 ===
    {"name": "科技自立自强/举国体制", "name_en": "Tech Self-Reliance", "category": "科技创新战略", "year": 2020,
     "region": "全国", "description": "关键核心技术攻关", "key_goals": "芯片,操作系统,工业软件自主可控",
     "risk": "中",
     "opportunities": [
         {"sector": "半导体", "title": "芯片自主可控", "type": "行业", "desc": "半导体设备、材料、EDA", "instruments": "688981.SH,688012.SH,688041.SH", "etfs": "512480", "risk": "高", "return": "高", "horizon": "长期"},
         {"sector": "操作系统", "title": "国产基础软件", "type": "行业", "desc": "鸿蒙、统信UOS、数据库", "instruments": "688111.SH,300378.SZ", "risk": "中", "return": "高", "horizon": "长期"},
     ]},
    {"name": "人工智能发展规划", "name_en": "AI Development Plan", "category": "科技创新战略", "year": 2017,
     "region": "全国", "description": "新一代AI发展规划", "key_goals": "2030年AI世界领先水平",
     "risk": "中",
     "opportunities": [
         {"sector": "AI", "title": "人工智能产业", "type": "行业", "desc": "大模型、AI应用、自动驾驶", "instruments": "002230.SZ,688256.SH,301269.SZ", "etfs": "159819", "risk": "中", "return": "高", "horizon": "中期"},
     ]},
    {"name": "量子科技发展战略", "name_en": "Quantum Technology Strategy", "category": "科技创新战略", "year": 2020,
     "region": "全国", "description": "量子计算、量子通信、量子测量", "key_goals": "量子科技全球领先",
     "risk": "高",
     "opportunities": [
         {"sector": "量子", "title": "量子科技产业化", "type": "前沿", "desc": "量子通信、量子计算", "instruments": "688027.SH,600990.SH", "risk": "高", "return": "高", "horizon": "长期"},
     ]},
    {"name": "北斗卫星导航系统", "name_en": "BeiDou Navigation System", "category": "科技创新战略", "year": 2020,
     "region": "全球", "description": "自主卫星导航系统", "key_goals": "GPS替代,民用推广",
     "risk": "低",
     "opportunities": [
         {"sector": "卫星导航", "title": "北斗应用产业", "type": "行业", "desc": "芯片、终端、高精度定位", "instruments": "002151.SZ,300627.SZ", "risk": "中", "return": "中", "horizon": "中期"},
     ]},
    {"name": "商业航天战略", "name_en": "Commercial Space", "category": "科技创新战略", "year": 2024,
     "region": "全国", "description": "商业航天市场化发展", "key_goals": "卫星互联网,可回收火箭",
     "risk": "高",
     "opportunities": [
         {"sector": "航天", "title": "商业航天产业", "type": "前沿", "desc": "卫星制造、火箭发射、卫星互联网", "instruments": "600118.SH,002025.SZ", "risk": "高", "return": "高", "horizon": "长期"},
     ]},
    {"name": "低空经济", "name_en": "Low-Altitude Economy", "category": "科技创新战略", "year": 2024,
     "region": "全国", "description": "eVTOL、无人机物流等低空产业", "key_goals": "低空空域开放,产业化",
     "risk": "高",
     "opportunities": [
         {"sector": "低空", "title": "eVTOL与无人机", "type": "前沿", "desc": "亿航智能、小鹏汇天、无人机物流", "instruments": "EH,002097.SZ", "risk": "高", "return": "高", "horizon": "长期"},
     ]},

    # === 民生与社会战略 ===
    {"name": "新型城镇化战略", "name_en": "New Urbanization", "category": "民生与社会战略", "year": 2014,
     "region": "全国", "description": "以人为核心的城镇化", "key_goals": "户籍改革,城市群发展",
     "risk": "低",
     "opportunities": [
         {"sector": "城市更新", "title": "老旧小区改造", "type": "基建", "desc": "城市更新、老旧小区改造、管网更新", "instruments": "002271.SZ", "risk": "低", "return": "中", "horizon": "中期"},
     ]},
    {"name": "三孩政策与人口战略", "name_en": "Three-Child Policy", "category": "民生与社会战略", "year": 2021,
     "region": "全国", "description": "应对人口老龄化", "key_goals": "鼓励生育,完善托幼",
     "risk": "中",
     "opportunities": [
         {"sector": "养老", "title": "银发经济", "type": "趋势", "desc": "养老服务、康复医疗、养老金融", "instruments": "600867.SH", "risk": "低", "return": "中", "horizon": "长期"},
     ]},
    {"name": "教育双减政策", "name_en": "Double Reduction Policy", "category": "民生与社会战略", "year": 2021,
     "region": "全国", "description": "减轻义务教育阶段学生课业负担", "key_goals": "规范校外培训",
     "risk": "中",
     "opportunities": [
         {"sector": "素质教育", "title": "素质教育与职业教育", "type": "趋势", "desc": "体育、艺术、STEAM教育转型", "instruments": "003032.SZ", "risk": "中", "return": "中", "horizon": "中期"},
     ]},
    {"name": "房住不炒与保障性住房", "name_en": "Housing Policy", "category": "民生与社会战略", "year": 2016,
     "region": "全国", "description": "建立租购并举住房制度", "key_goals": "保障性租赁住房,共有产权房",
     "risk": "中",
     "opportunities": [
         {"sector": "保障房", "title": "保障性住房REITs", "type": "金融", "desc": "保障性租赁住房公募REITs", "instruments": "508000.SH,508077.SH", "risk": "低", "return": "中", "horizon": "长期"},
     ]},

    # === 安全与治理战略 ===
    {"name": "粮食安全战略", "name_en": "Food Security Strategy", "category": "安全与治理战略", "year": 2014,
     "region": "全国", "description": "确保谷物基本自给", "key_goals": "种业振兴,耕地红线,粮食储备",
     "risk": "低",
     "opportunities": [
         {"sector": "种业", "title": "种业振兴", "type": "行业", "desc": "转基因种子商业化、种业龙头", "instruments": "000998.SZ,600598.SH", "risk": "中", "return": "中", "horizon": "长期"},
     ]},
    {"name": "能源安全战略", "name_en": "Energy Security Strategy", "category": "安全与治理战略", "year": 2014,
     "region": "全国", "description": "能源革命与安全保障", "key_goals": "油气增储上产,新能源替代",
     "risk": "中",
     "opportunities": [
         {"sector": "能源", "title": "油气增储上产", "type": "行业", "desc": "页岩油气、深海油气开发", "instruments": "601857.SH,600028.SH", "risk": "中", "return": "中", "horizon": "中期"},
         {"sector": "核电", "title": "核电重启", "type": "行业", "desc": "三代核电批量化建设", "instruments": "601985.SH,601611.SH", "risk": "中", "return": "中", "horizon": "长期"},
     ]},
    {"name": "国防和军队现代化", "name_en": "Military Modernization", "category": "安全与治理战略", "year": 2020,
     "region": "全国", "description": "2027年实现建军百年奋斗目标", "key_goals": "装备现代化,信息化,智能化",
     "risk": "中",
     "opportunities": [
         {"sector": "军工", "title": "国防军工产业", "type": "行业", "desc": "航空、航天、船舶、电子信息", "instruments": "600760.SH,601989.SH,600893.SH", "etfs": "512660", "risk": "中", "return": "中", "horizon": "长期"},
     ]},
    {"name": "网络强国与数据安全", "name_en": "Cyber Security Strategy", "category": "安全与治理战略", "year": 2014,
     "region": "全国", "description": "网络安全和信息化", "key_goals": "关键信息基础设施保护,数据安全",
     "risk": "中",
     "opportunities": [
         {"sector": "网安", "title": "网络安全产业", "type": "行业", "desc": "安全产品与服务", "instruments": "002439.SZ,688561.SH,300454.SZ", "risk": "中", "return": "中", "horizon": "中期"},
     ]},
    {"name": "西部大开发(新时代)", "name_en": "Western Development 2.0", "category": "安全与治理战略", "year": 2020,
     "region": "西部12省区", "description": "新时代西部大开发", "key_goals": "大保护,大开放,高质量发展",
     "risk": "中",
     "opportunities": [
         {"sector": "清洁能源", "title": "西部风光大基地", "type": "行业", "desc": "沙漠戈壁大型风电光伏基地", "instruments": "601012.SH,600905.SH", "risk": "中", "return": "高", "horizon": "中期"},
     ]},
    {"name": "东北全面振兴", "name_en": "Northeast Revitalization", "category": "安全与治理战略", "year": 2023,
     "region": "东北三省", "description": "新时代东北全面振兴", "key_goals": "产业转型,人口流失应对,国企改革",
     "risk": "高", "opportunities": []},
    {"name": "中部地区崛起", "name_en": "Central Region Rise", "category": "安全与治理战略", "year": 2024,
     "region": "中部六省", "description": "新时代中部地区崛起", "key_goals": "先进制造,粮食安全,交通枢纽",
     "risk": "中",
     "opportunities": [
         {"sector": "制造", "title": "中部先进制造业", "type": "行业", "desc": "武汉光谷、长株潭、合肥新能源", "instruments": "000988.SZ", "risk": "中", "return": "中", "horizon": "中期"},
     ]},
]


def seed_data():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM policy_categories")
    if cursor.fetchone()[0] > 0:
        print("Database already seeded, skipping...")
        conn.close()
        return

    for cat in CATEGORIES:
        cursor.execute(
            "INSERT INTO policy_categories (name, name_en, description, sort_order) VALUES (?, ?, ?, ?)",
            (cat["name"], cat["name_en"], cat["description"], cat["sort_order"])
        )

    cat_map = {}
    cursor.execute("SELECT id, name FROM policy_categories")
    for row in cursor.fetchall():
        cat_map[row["name"]] = row["id"]

    for p in POLICIES:
        category_id = cat_map[p["category"]]
        cursor.execute("""
            INSERT INTO policies (name, name_en, category_id, established_year, region, description,
                key_goals, total_investment_billion, gdp_billion, fiscal_revenue_billion, debt_billion,
                risk_level, overall_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["name"], p.get("name_en"), category_id, p.get("year"), p.get("region"),
            p.get("description"), p.get("key_goals"),
            p.get("total_investment"), p.get("gdp"), p.get("fiscal_revenue"), p.get("debt"),
            p.get("risk", "中"), None
        ))
        policy_id = cursor.lastrowid

        for opp in p.get("opportunities", []):
            cursor.execute("""
                INSERT INTO investment_opportunities
                    (policy_id, sector, opportunity_type, title, description, risk_level,
                     potential_return, time_horizon, recommended_instruments, key_etfs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                policy_id, opp["sector"], opp.get("type"), opp["title"],
                opp.get("desc"), opp.get("risk", "中"), opp.get("return", "中"),
                opp.get("horizon", "中期"), opp.get("instruments", ""),
                opp.get("etfs", "")
            ))

    conn.commit()
    total_policies = cursor.execute("SELECT COUNT(*) FROM policies").fetchone()[0]
    total_opps = cursor.execute("SELECT COUNT(*) FROM investment_opportunities").fetchone()[0]
    print(f"Seeded {total_policies} policies and {total_opps} investment opportunities")
    conn.close()


if __name__ == "__main__":
    seed_data()
