# cnloc (China Location)

Last updated on 2025-12-04

`cnloc` 是一个专注于中国地址解析的Python库，核心功能如下：  
- 解析地址文本，提取省份、城市、区县的**全称**、**行政区划代码**及 **ID** 
- 解析原则：兼顾**全面性**与**准确性**，尽可能匹配完整地址信息，确保已有的匹配结果100%准确，模糊场景下不强行匹配   
- 支持按指定年份匹配（覆盖1980-2024年历史行政区划）  
- 提供两种匹配模式（左到右匹配/低到高匹配）  


`cnloc` is a Python package dedicated to Chinese address parsing, with core features including:  
- Parses address text to extract **full name** (_name), **short name** (_short), **administrative division code** (adcode), and **ID** for provinces, cities, and counties  
- Parsing principle: Balance **comprehensiveness** and **accuracy**; match as much complete address information as possible while ensuring 100% accuracy of results; no forced matching for ambiguous scenarios  
- Supports year-specific matching (covering historical administrative divisions from 1980 to 2024)  
- Offers two matching modes (left-to-right matching / low-to-high matching)



## 使用说明 | Usage  

下载安装 Installation
```bash
pip install cnloc
```


一个简单的例子 A simple example:
```python
import cnloc
result = cnloc.parse('广东省深圳市南山区深南大道')
result
```

| address                     | year | province_name | city_name | county_name | province_adcode | city_adcode | county_adcode | province_id | city_id | county_id |
|-----------------------------|------|---------------|-----------|-------------|-----------------|-------------|---------------|-------------|---------|-----------|
| 广东省深圳市南山区深南大道 | 2024 | 广东省        | 深圳市    | 南山区      | 440000          | 440300      | 440305        | 440000      | 440300  | 440305    |


注意：`county_id`（区县ID）目前暂不可靠！省份、城市ID已完成人工核对。 

Note: County-level IDs `county_id` are currently **unreliable**! Province- and city-level IDs have been manually verified.


一个更复杂的例子 A more complex example
```python
import cnloc
address_data = ['江苏省昆山市千灯镇玉溪西路', '广东省深圳市南山区深南大道']
result = cnloc.getlocation(address_data, year=2023, mode=1)
result
```

| address                   | year | province_name | city_name | county_name | province_adcode | city_adcode | county_adcode | province_id | city_id | county_id |
|---------------------------|------|---------------|-----------|-------------|-----------------|-------------|---------------|-------------|---------|-----------|
| 江苏省昆山市千灯镇玉溪西路 | 2023 | 江苏省        | 苏州市    | 昆山市      | 320000          | 320500      | 320583        | 320000      | 320500  | 320583    |
| 广东省深圳市南山区深南大道 | 2023 | 广东省        | 深圳市    | 南山区      | 440000          | 440300      | 440305        | 440000      | 440300  | 440305    |

具体参数介绍详见包文档。

Detailed parameter descriptions are available in the package documentation.


未来规划：
- 完善县级ID数据  
- 支持开发区、道路等经济地理相关匹配  
- 扩展乡镇、村社级地址匹配  

Future plans:
- Complete county-level ID data  
- Support matching for development zones, roads, and other economic and geographic entities  
- Extend to town- and village-level address matching




## 开发背景 | Background  

Python中主流的中文地址解析库为[cpca](https://github.com/DQinYuan/chinese_province_city_area_mapper)，但在实际使用中存在以下局限性：  
- 地址库更新停滞：自2021年起未更新，受限于数据源[adcode](https://github.com/Vonng/adcode)的年份限制，缺失大量历史数据  
- 数据无年份区分：不同年份的行政区划数据混合存储，无法追溯历史归属  
- 匹配规则单一：仅支持区县全称匹配，不兼容区县简称  
- 模糊场景处理不当：多结果匹配时强行返回单一结果，存在准确性风险
- 数据维度不足：仅包含全称与行政区划代码，缺少ID等关键字段。ID在经济学研究中至关重要，可追溯城市历史变迁，避免因名称/代码变更导致的数据断裂  

鉴于上述局限性，本项目参考`cpca`的逻辑，开发了cnloc库以满足更精准、全面的地址解析需求。  


The mainstream Chinese address parsing library in Python is [cpca](https://github.com/DQinYuan/chinese_province_city_area_mapper), but it has the following limitations in practical use:  
- Stagnant address database updates: No updates since 2021; limited by the year range of its data source [adcode](https://github.com/Vonng/adcode), missing a large amount of historical data  
- No year distinction for data: Administrative division data from different years are stored mixed, making it impossible to trace historical affiliations  
- Single matching rule: Only supports full-name matching for counties/districts, not compatible with short names  
- Improper handling of ambiguous scenarios: Forcibly returns a single result when multiple matches exist, posing accuracy risks  
- Insufficient data dimensions: Only includes full names and administrative division codes, lacking key fields such as IDs. IDs are particularly critical in economic research, as they enable tracing the historical changes of cities and avoid data disruption caused by name/code changes 

To address these limitations, `cnloc` was developed with reference to `cpca`'s logic to meet the needs of more accurate and comprehensive address parsing.


以下简单示例对比cnloc与cpca的解析效果，可直观体现性能差异：

The following simple example compares the parsing results of `cnloc` and `cpca` to intuitively demonstrate functional differences:  

```python
address_data = [
    "朝阳", '朝阳市', '朝阳县', '朝阳区', '朝阳市朝阳', '朝阳朝阳', '北京朝阳', '辽宁朝阳',
    '荆州', '荆州市', '荆州区', '荆州市荆州区', '荆州市荆州', "荆州荆州", "荆州荆州区", '湖北荆州', '湖北荆州沙市', 
    "鼓楼区", "江苏鼓楼区","南京鼓楼区", "江苏徐州鼓楼区",
    '南山', "广东省深圳市南山区深南大道", "深圳南山", "广东南山", '深圳市华侨城东部工业区', '深圳东门南路2006号宝丰大厦五楼', "中国深圳市深南大道",  
    '海淀', "北京市海淀区中关村大街1号", "海淀中关村大街1号", '中关村大街1号',
    '马鞍山市经济技术开发区红旗南路51号', '银川市西夏区北京西路630号', '杭州市延安路508号', '江苏省昆山市千灯镇玉溪西路168号', "上海市", '' 
]

# Parse with cnloc
import cnloc
cnloc.getlocation(address_data)

# Parse with cpca
import cpca
cpca.transform(address_data) 
```

| Address | cnloc-Province | cnloc-City | cnloc-County | cpca-Province | cpca-City | cpca-County |
|---------|----------------|------------|--------------|---------------|-----------|-------------|
| 朝阳 |  |  |  | **辽宁省** | **朝阳市** |  |
| 朝阳市 | 辽宁省 | 朝阳市 |  | 辽宁省 | 朝阳市 |  |
| 朝阳县 | 辽宁省 | 朝阳市 | 朝阳县 | 辽宁省 | 朝阳市 | 朝阳县 |
| 朝阳区 |  |  |  | **吉林省** | **长春市** | **朝阳区** |
| 朝阳市朝阳 | 辽宁省 | 朝阳市 | 朝阳县 | 辽宁省 | 朝阳市 | **Missing** |
| 朝阳朝阳 | 辽宁省 | 朝阳市 | 朝阳县 | 辽宁省 | 朝阳市 | **Missing** |
| 北京朝阳 | 北京市 | 市辖区 | 朝阳区 | 北京市 | **Missing** | **Missing** |
| 辽宁朝阳 | 辽宁省 | 朝阳市 |  | 辽宁省 | 朝阳市 |  |
| 荆州 | 湖北省 | 荆州市 |  | 湖北省 | 荆州市 |  |
| 荆州市 | 湖北省 | 荆州市 |  | 湖北省 | 荆州市 |  |
| 荆州区 | 湖北省 | 荆州市 | 荆州区 | 湖北省 | 荆州市 | 荆州区 |
| 荆州市荆州区 | 湖北省 | 荆州市 | 荆州区 | 湖北省 | 荆州市 | 荆州区 |
| 荆州市荆州 | 湖北省 | 荆州市 | 荆州区 | 湖北省 | 荆州市 | **Missing** |
| 荆州荆州 | 湖北省 | 荆州市 | 荆州区 | 湖北省 | 荆州市 | **Missing** |
| 荆州荆州区 | 湖北省 | 荆州市 | 荆州区 | 湖北省 | 荆州市 | 荆州区 |
| 湖北荆州 | 湖北省 | 荆州市 |  | 湖北省 | 荆州市 |  |
| 湖北荆州沙市 | 湖北省 | 荆州市 | 沙市区 | 湖北省 | 荆州市 | **Missing** |
| 鼓楼区 |  |  |  | **河南省** | **开封市** | **鼓楼区** |
| 江苏鼓楼区 | 江苏省 |  |  | 江苏省 | **南京市** | **鼓楼区** |
| 南京鼓楼区 | 江苏省 | 南京市 | 鼓楼区 | 江苏省 | 南京市 | 鼓楼区 |
| 江苏徐州鼓楼区 | 江苏省 | 徐州市 | 鼓楼区 | 江苏省 | 徐州市 | 鼓楼区 |
| 南山 |  |  |  |  |  |  |
| 广东省深圳市南山区深南大道 | 广东省 | 深圳市 | 南山区 | 广东省 | 深圳市 | 南山区 |
| 深圳南山 | 广东省 | 深圳市 | 南山区 | 广东省 | 深圳市 | **Missing** |
| 广东南山 | 广东省 | 深圳市 | 南山区 | 广东省 | **Missing** | **Missing** |
| 深圳市华侨城东部工业区 | 广东省 | 深圳市 |  | 广东省 | 深圳市 |  |
| 深圳东门南路2006号宝丰大厦五楼 | 广东省 | 深圳市 |  | 广东省 | 深圳市 |  |
| 中国深圳市深南大道 | 广东省 | 深圳市 |  | 广东省 | 深圳市 |  |
| 海淀 | 北京市 | 市辖区 | 海淀区 | **Missing** | **Missing** | **Missing** |
| 北京市海淀区中关村大街1号 | 北京市 | 市辖区 | 海淀区 | 北京市 | 市辖区 | 海淀区 |
| 海淀中关村大街1号 | 北京市 | 市辖区 | 海淀区 | **Missing** | **Missing** | **Missing** |
| 中关村大街1号 |  |  |  |  |  |  |
| 马鞍山市经济技术开发区红旗南路51号 | 安徽省 | 马鞍山市 |  | 安徽省 | 马鞍山市 |  |
| 银川市西夏区北京西路630号 | 宁夏回族自治区 | 银川市 | 西夏区 | 宁夏回族自治区 | 银川市 | 西夏区 |
| 杭州市延安路508号 | 浙江省 | 杭州市 |  | 浙江省 | 杭州市 |  |
| 江苏省昆山市千灯镇玉溪西路168号 | 江苏省 | 苏州市 | 昆山市 | 江苏省 | 苏州市 | 昆山市 |
| 上海市 | 上海市 |  |  | 上海市 |  |  |



## 数据质量 | Data Quality  

数据来源：
- 1980-2024年度行政区划代码：爬取自[中华人民共和国民政部行政区划代码](https://www.mca.gov.cn/n156/n186/index.html)，人工修正部分官方错误数据
- 官方行政区划数目：来自[中华人民共和国国家统计局年度数据](https://data.stats.gov.cn/easyquery.htm?cn=C01)  
  
Data Sources:
- Administrative division codes (1980-2024): Scraped from [Ministry of Civil Affairs of the People's Republic of China](https://www.mca.gov.cn/n156/n186/index.html), with manual corrections for partial official errors
- Official administrative division counts: Sourced from [National Bureau of Statistics of the People's Republic of China Annual Data](https://data.stats.gov.cn/easyquery.htm?cn=C01)


地级行政区划数目对比 Comparison of city-level administrative divisions  

| Year     | 1980 | 1981 | 1982 | 1983 | 1984 | 1985 | 1986 | 1987 | 1988 | 1989 | 1990 | 1991 | 1992 | 1993 | 1994 | 1995 | 1996 | 1997 | 1998 | 1999 | 2000 | 2001 | 2002 | 2003 | 2004 | 2005 | 2006 | 2007 | 2008 | 2009 | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|----------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|
| Official | 318  | 316  | 322  | 322  | 322  | 327  | 325  | 326  | 334  | 336  | 336  | 338  | 339  | 335  | 333  | 340  | 335  | 332  | 331  | 331  | 333  | 332  | 332  | 333  | 333  | 333  | 333  | 333  | 333  | 333  | 333  | 332  | 333  | 333  | 333  | 334  | 334  | 334  | 333  | 333  | 333  | 333  | 333  | 333  | 333 |
| My       | **316**  | 316  | **319**  | **323**  | **323**  | 327  | **324**  | 326  | 334  | 336  | 336  | 338  | 339  | 335  | 333  | **334**  | 335  | 332  | 331  | 331  | 333  | 332  | 332  | 333  | 333  | 333  | 333  | 333  | 333  | 333  | 333  | 332  | 333  | 333  | 333  | 334  | 334  | 334  | 333  | 333  | 333  | 333  | 333  | 333  | 333 |

县级行政区划数目对比 Comparison of county-level administrative divisions  

| Year     | 1980 | 1981 | 1982 | 1983 | 1984 | 1985 | 1986 | 1987 | 1988 | 1989 | 1990 | 1991 | 1992 | 1993 | 1994 | 1995 | 1996 | 1997 | 1998 | 1999 | 2000 | 2001 | 2002 | 2003 | 2004 | 2005 | 2006 | 2007 | 2008 | 2009 | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|----------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|------|
| Official | 2775 | 2780 | 2797 | 2785 | 2814 | 2826 | 2830 | 2826 | 2831 | 2829 | 2833 | 2833 | 2833 | 2835 | 2845 | 2849 | 2859 | 2862 | 2863 | 2858 | 2861 | 2861 | 2860 | 2861 | 2862 | 2862 | 2860 | 2859 | 2859 | 2858 | 2856 | 2853 | 2852 | 2853 | 2854 | 2850 | 2851 | 2851 | 2851 | 2846 | 2844 | 2843 | 2843 | 2844 | 2846 |
| My       | **2761** | **2772** | **2793** | **2774** | **2813** | **2825** | **2831** | 2826 | **2830** | 2829 | 2833 | 2833 | 2833 | 2835 | 2845 | 2849 | **2858** | 2862 | 2863 | 2858 | 2861 | 2861 | 2860 | 2861 | 2862 | 2862 | 2860 | 2859 | 2859 | 2858 | 2856 | 2853 | 2852 | 2853 | 2854 | 2850 | 2851 | 2851 | 2851 | 2846 | 2844 | 2843 | 2843 | 2844 | 2846 |


## 参考资料 | References

- [cpca](https://github.com/DQinYuan/chinese_province_city_area_mapper)
- [Administrative-divisions-of-China](https://github.com/modood/Administrative-divisions-of-China)
- [china_area](https://github.com/adyliu/china_area)
- [gbt2260](https://github.com/medz/gbt2260)
- [中华人民共和国行政区划沿革地图集（1949~1999）， 陈潮、陈洪玲主编，中国地图出版社](https://book.douban.com/subject/1139251/)
- [知乎：行政区划代码历史大全（民政部1980年-2024年+老国标+非官方数据）及一些历史梳理挖掘（2025.05更新）](https://zhuanlan.zhihu.com/p/564774073)




