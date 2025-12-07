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



# cd "C:/Dropbox/CodeCenter/Python/src/cnloc/"
# python -m build
# twine upload dist/*