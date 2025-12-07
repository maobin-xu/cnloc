import sys
sys.path.append("C:/Dropbox/CodeCenter/Python/src/cnloc/")
import cnloc
address_data = [
    "朝阳", '朝阳市', '朝阳县', '朝阳区', '朝阳市朝阳', '朝阳朝阳', '北京朝阳', '辽宁朝阳',
    '荆州', '荆州市', '荆州区', '荆州市荆州区', '荆州市荆州', "荆州荆州", "荆州荆州区", '湖北荆州', '湖北荆州沙市', 
    "鼓楼区", "江苏鼓楼区","南京鼓楼区", "江苏徐州鼓楼区",
    '南山', "广东省深圳市南山区深南大道", "深圳南山", "广东南山", '深圳市华侨城东部工业区', '深圳东门南路2006号宝丰大厦五楼', "中国深圳市深南大道",  
    '海淀', "北京市海淀区中关村大街1号", "海淀中关村大街1号", '中关村大街1号',
    '马鞍山市经济技术开发区红旗南路51号', '银川市西夏区北京西路630号', '杭州市延安路508号', '江苏省昆山市千灯镇玉溪西路168号', "上海市", '' ]
data1 = cnloc.getlocation( address_data) 

import cpca
data2 = cpca.transform( address_data )

import pandas as pd
df_compare = pd.concat( [data1[['address', 'province_name', 'city_name', 'county_name']], data2[['省','市','区']]], axis=1 )




def generate_balanced_md_table(your_df, cpca_df, your_addr_col='address', 
                               your_prov_col='province_name', your_city_col='city_name', your_county_col='county_name',
                               cpca_prov_col='省', cpca_city_col='市', cpca_county_col='区'):
    """生成带合并表头的Markdown表格：差异内容加粗（无HTML，纯MD）"""
    # 1. 数据合并与空值处理
    merged_df = pd.concat([
        your_df[[your_addr_col, your_prov_col, your_city_col, your_county_col]],
        cpca_df[[cpca_prov_col, cpca_city_col, cpca_county_col]]
    ], axis=1)
    merged_df = merged_df.replace({pd.NA: None, float('nan'): None})
    
    # 2. 定义加粗逻辑（替代标红）
    def bold_diff(cpca_val, your_val):
        if cpca_val is None and your_val is None:
            return ""
        elif your_val and not cpca_val:
            return "**Missing**"  # 你有值cpca无值 → 加粗Missing
        elif not your_val and cpca_val:
            return f"**{cpca_val}**"  # 你空cpca有值 → 加粗cpca值
        elif cpca_val != your_val:
            return f"**{cpca_val}**"  # 两者值不同 → 加粗cpca值
        else:
            return cpca_val if cpca_val else ""
    
    # 3. 应用加粗逻辑
    styled_df = merged_df.copy()
    styled_df[cpca_prov_col] = [bold_diff(c, y) for c, y in zip(styled_df[cpca_prov_col], styled_df[your_prov_col])]
    styled_df[cpca_city_col] = [bold_diff(c, y) for c, y in zip(styled_df[cpca_city_col], styled_df[your_city_col])]
    styled_df[cpca_county_col] = [bold_diff(c, y) for c, y in zip(styled_df[cpca_county_col], styled_df[your_county_col])]
    
    # 4. 生成Markdown表格（带合并表头注释，纯MD格式）
    md = []
    # 表头说明（兼容MD合并表头的写法）
    md.append("| Address | cnloc-Province | cnloc-City | cnloc-County | cpca-Province | cpca-City | cpca-County |")
    md.append("|---------|----------------|------------|--------------|---------------|-----------|-------------|")
    
    # 表体数据（每行占一行，无多余空行）
    for _, row in styled_df.iterrows():
        addr = row[your_addr_col] if row[your_addr_col] else ''
        c_prov = row[your_prov_col] if row[your_prov_col] else ''
        c_city = row[your_city_col] if row[your_city_col] else ''
        c_county = row[your_county_col] if row[your_county_col] else ''
        p_prov = row[cpca_prov_col] if row[cpca_prov_col] else ''
        p_city = row[cpca_city_col] if row[cpca_city_col] else ''
        p_county = row[cpca_county_col] if row[cpca_county_col] else ''
        
        # 拼接MD行（特殊字符转义，确保格式正确）
        md.append(f"| {addr} | {c_prov} | {c_city} | {c_county} | {p_prov} | {p_city} | {p_county} |")
    
    # 拼接为字符串（仅保留必要换行）
    return '\n'.join(md)

# ---------------------- 使用示例 ----------------------
balanced_md = generate_balanced_md_table(
    your_df=data1,
    cpca_df=data2,
    your_addr_col='address',
    your_prov_col='province_name',
    your_city_col='city_name',
    your_county_col='county_name',
    cpca_prov_col='省',
    cpca_city_col='市',
    cpca_county_col='区'
)

# 打印Markdown表格（直接复制粘贴到MD文档）
print(balanced_md)



