# # update user_dict
# user_location = [
#     {'name':"空港经济区", 'year_begin': 2010, 'year_end': DEFAULT_YEAR, 'province': '天津市', 'city': '市辖区', 'county': '滨海新区'},
#     {'name':"经济技术开发区", 'year_begin': 2009, 'year_end': DEFAULT_YEAR, 'province': '天津市', 'city': '市辖区', 'county': '滨海新区'},
#     {'name':"自由贸易区", 'year_begin': 2013, 'year_end': DEFAULT_YEAR, 'province': '上海市', 'city': '市辖区', 'county': '浦东新区'},
#     {'name':"张江高科技园区", 'year_begin': 2009, 'year_end': DEFAULT_YEAR, 'province': '上海市', 'city': '市辖区', 'county': '浦东新区'},  
#     {'name':"中关村大街", 'year_begin': 2000, 'year_end': DEFAULT_YEAR, 'province': '北京市', 'city': '市辖区', 'county': '海淀区'},
#     {'name':"深南东路", 'year_begin': 2000, 'year_end': DEFAULT_YEAR, 'province': '广东省', 'city': '深圳市', 'county': '罗湖区'}
# ]
# for each_address in user_location:
#     each_name = each_address['name']
#     each_province_name = each_address['province']
#     each_city_name = each_address['city']
#     each_county_name = each_address['county']
#     each_county_adcode = each_address['county']
    
#     for each_year in range(each_address['year_begin'], each_address['year_end']+1):
#         if each_year in years_to_build:
#             for year, location_info in self.adcode_to_location.items():
#                 province_name = location_info['province_name']
#                 city_name = location_info['city_name']
#                 county_name = location_info['county_name']
#                 county_adcode = location_info['county_adcode']
#                 if (year == each_year and province_name==each_province_name and city_name==each_city_name and county_name==each_county_name) or (year == each_year and county_adcode==each_county_adcode):
#                     year_name_to_adcode[each_year][each_name][(FULL_NAME, 'county')].append(county_adcode)

# import pyreadstat
# data, meta = pyreadstat.read_dta(
#     'D:/MySystem/MyData/China_firm_year_CSMAR_20251001.dta',
#     encoding='utf-8',  # 关键：指定编码
#     usecols=['registeraddress', 'officeaddress']  # 只读取需要的列
# )
# data = data[data['officeaddress']!='']
# data

import sys
sys.path.append("C:/Dropbox/CodeCenter/Python/src/cnloc/")
import cnloc

address_data = [
    "朝阳", '朝阳市', '朝阳县', '朝阳区', '朝阳市朝阳', '朝阳朝阳', '北京朝阳', '辽宁朝阳',
    '荆州', '荆州市', '荆州区', '荆州市荆州区', '荆州市荆州', "荆州荆州", "荆州荆州区", '湖北荆州', '湖北荆州沙市', 
    "鼓楼区", "江苏鼓楼区","南京鼓楼区", "江苏徐州鼓楼区",
    '南山', "广东省深圳市南山区深南大道", "深圳南山", "广东南山", '深圳市华侨城东部工业区', '深圳东门南路2006号宝丰大厦五楼', "中国深圳市深南大道",  
    '海淀', "北京市海淀区中关村大街1号", "海淀中关村大街1号", '中关村大街1号',
    '马鞍山市经济技术开发区红旗南路51号', '银川市西夏区北京西路630号', '杭州市延安路508号', '江苏省昆山市千灯镇玉溪西路168号', "上海市", '' 
]
cnloc.getlocation(address_data, drop=['adcode','id'], county_short=True)


# cd "C:/Dropbox/CodeCenter/Python/src/cnloc/"
# python -m build
# twine upload dist/*