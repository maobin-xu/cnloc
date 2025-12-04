"""
cnloc
中国行政区划地址解析器
Address Parser for Chinese Administrative Divisions
"""
__version__ = "0.1.4"

import pandas as pd
import ahocorasick
import csv
from importlib.resources import files
from collections import defaultdict
from typing import Union, Optional, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor

# --- Constants ---
RANK_PROVINCE, RANK_CITY, RANK_COUNTY = 1, 2, 3  # administrative levels: province, city, county
FULL_NAME, SHORT_NAME = 1, 2  # name types: full name, short name
DEFAULT_YEAR = 2024  # default year for address parsing
LEFT_TO_RIGHT, LOW_TO_HIGH = 1, 2  # matching modes: left-to-right, low-to-high


class AddressParser:
    """
    Address Parser for Chinese Administrative Divisions
    Uses Aho-Corasick for efficient matching and supports batch processing.
    """

    # singleton implementation
    _instance: Optional['AddressParser'] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance is created (Singleton)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the AddressParser."""
        if not AddressParser._initialized:
            # save automaton by year
            self.year_automatons: Dict[int, ahocorasick.Automaton] = {}  # { year: ahocorasick.Automaton }
            # load data and build adcode_to_location
            self.adcode_to_location: Dict[Tuple[int, str], dict] = {}  # { (year, adcode): location_info_dict }
            self._load_data()
            # initialized
            AddressParser._initialized = True

    def _load_data(self: int) -> None:
        # load data and preprocess by row
        path = files("cnloc.data").joinpath("location_year_20251001.csv")
        with open(path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rank = int(row['rank'])
                year = int(row['year'])
                adcode = None
                # consolidate location info extraction
                location_fields = [
                    'province_name', 'province_short', 'province_adcode', 'province_id',
                    'city_name', 'city_short', 'city_adcode', 'city_id',
                    'county_name', 'county_short', 'county_adcode', 'county_id'
                ]
                location_info = {field: row[field] if row[field] != '' else None for field in location_fields}
                location_info['rank'] = rank  # explicitly add rank
                # update adcode_to_location
                if rank == RANK_PROVINCE:
                    adcode = location_info['province_adcode']
                elif rank == RANK_CITY:
                    if location_info['city_adcode'] != '460000':  # 海南省直辖县的city adcode, conflict with province adcode
                        adcode = location_info['city_adcode']
                elif rank == RANK_COUNTY:
                    adcode = location_info['county_adcode']
                if adcode:
                    self.adcode_to_location[(year, adcode)] = location_info

    def _build_automaton(self, match_year_list: List[int]):
        # structure: year -> name -> {(mode, rank_str): [adcodes]}
        year_name_to_adcode = defaultdict(
            lambda: defaultdict(
                lambda: {
                    (FULL_NAME, 'province'): [], (SHORT_NAME, 'province'): [],
                    (FULL_NAME, 'city'): [], (SHORT_NAME, 'city'): [],
                    (FULL_NAME, 'county'): [], (SHORT_NAME, 'county'): []
                }
            )
        )
        
        # filter years that need to be built
        years_to_build = list(set(match_year_list) - set(self.year_automatons.keys()))
        if not years_to_build:
            return

        # build year_name_to_adcode
        for (year, adcode), location_info in self.adcode_to_location.items():
            if year in years_to_build:
                if location_info['rank'] == RANK_PROVINCE:
                    year_name_to_adcode[year][location_info['province_name']][(FULL_NAME, 'province')].append(adcode)
                    year_name_to_adcode[year][location_info['province_short']][(SHORT_NAME, 'province')].append(adcode)
                elif location_info['rank'] == RANK_CITY:
                    year_name_to_adcode[year][location_info['city_name']][(FULL_NAME, 'city')].append(adcode)
                    year_name_to_adcode[year][location_info['city_short']][(SHORT_NAME, 'city')].append(adcode)
                elif location_info['rank'] == RANK_COUNTY:
                    year_name_to_adcode[year][location_info['county_name']][(FULL_NAME, 'county')].append(adcode)
                    year_name_to_adcode[year][location_info['county_short']][(SHORT_NAME, 'county')].append(adcode)

        # deduplicate adcodes and build automatons
        for year in years_to_build:
            # create automatons
            automaton = ahocorasick.Automaton()
            name_to_adcode = year_name_to_adcode[year]
            # add words to automaton
            for name, info in name_to_adcode.items():
                # deduplicate adcodes before adding to automaton
                dedup_info = {
                    key: list(set(adcodes)) for key, adcodes in info.items()
                }
                # only add if there are valid adcodes
                if dedup_info: 
                    automaton.add_word(name, {'name': name, 'adcode': dedup_info})
            # make automaton
            automaton.make_automaton()
            self.year_automatons[year] = automaton
 
    def get_best_matches(self, sentence: str, year: int = DEFAULT_YEAR) -> List[dict]:
        """
        Get best matches, keeping longest and non-overlapping matches
        """
        # collect all matches
        matches = []
        for end_idx, content in self.year_automatons[year].iter(sentence):
            start_idx = end_idx - len(content['name']) + 1
            matches.append({
                "start": start_idx,
                "end": end_idx,
                "name": content['name'],
                "adcode": content['adcode'],
                "length": end_idx - start_idx + 1  # string pattern length
            })
        
        # sort by start index ascending, length descending (prefer longer matches at the same start)
        matches.sort(key=lambda x: (x["start"], -x["length"]))
        
        # filter overlapping matches
        best_matches = []
        last_end = -1
        for match in matches:
            if match["start"] > last_end:
                best_matches.append(match)
                last_end = match["end"]
        
        return best_matches

    def get_location_from_adcode(self, province_adcode: str, city_adcode: str = None, county_adcode: str = None, year: int = DEFAULT_YEAR) -> dict:
        """
        Get location information for a given adcode
        """
        # by order of county, city, province
        for adcode in [county_adcode, city_adcode, province_adcode]: 
            if adcode:
                location = self.adcode_to_location[(year, adcode)].copy()
                location.pop('rank')
                location.pop('province_short')
                location.pop('city_short')
                location.pop('county_short')
                return location
        return {
            'province_name': None, 'province_adcode': None, 'province_id': None,
            'city_name': None, 'city_adcode': None, 'city_id': None,
            'county_name': None, 'county_adcode': None, 'county_id': None
        }

    def parse_left_to_right(self, matched_results: List[dict], year: int = DEFAULT_YEAR) -> dict:
        """
        Left-to-right matching mode: match province, city, county in address order
        """
        
        province_adcode, city_adcode, county_adcode = None, None, None

        def select_province_adcode(matched_adcodes):
            nonlocal province_adcode
            # select province adcode
            for each_province_adcode in matched_adcodes:
                if each_province_adcode:  # find province code
                    # update location information
                    province_adcode = each_province_adcode
                    return True
            return False
        def select_city_adcode(matched_adcodes, year, short=False):
            nonlocal province_adcode, city_adcode
            # select city adcode
            for each_city_adcode in matched_adcodes:
                if each_city_adcode:  # find city code
                    # other location information
                    location_infor = self.adcode_to_location[(year,each_city_adcode)]
                    current_province_adcode = location_infor['province_adcode']
                    # special cases: same-name county under same-name city, other city with same-name county
                    if short and location_infor['city_short']=='朝阳' and not province_adcode:
                        city_adcode = each_city_adcode
                        return True
                    # update location information
                    if (province_adcode==current_province_adcode) or (not province_adcode):
                        province_adcode = current_province_adcode
                        city_adcode = each_city_adcode
                        return True
            return False
        def select_county_adcode(matched_adcodes, year):
            nonlocal province_adcode, city_adcode, county_adcode
            # select county adcode
            for each_county_adcode in matched_adcodes:
                if each_county_adcode:  # find county code
                    # other location information
                    location_infor = self.adcode_to_location[(year,each_county_adcode)]
                    current_province_adcode = location_infor['province_adcode']
                    current_city_adcode = location_infor['city_adcode']
                    # update location information: 江苏省南京市鼓楼区(320106), 江苏省徐州市鼓楼区(320302)
                    if (province_adcode==current_province_adcode and city_adcode==current_city_adcode) or \
                       (province_adcode==current_province_adcode and not city_adcode and each_county_adcode not in ['320106','320302']) or \
                       (not province_adcode and city_adcode==current_city_adcode) or \
                       (not province_adcode and city_adcode==None and len(matched_adcodes)==1):
                        province_adcode = current_province_adcode
                        city_adcode = current_city_adcode
                        county_adcode = each_county_adcode
                        return True
            return False

        # matching from left to right
        for each_match in matched_results:
            adcode_map = each_match['adcode']
            # match province
            if not province_adcode:
                # full-name first, then short-name
                if select_province_adcode(adcode_map[(FULL_NAME, 'province')]) or select_province_adcode(adcode_map[(SHORT_NAME, 'province')]):
                    continue  # skip other matching if province is matched
            # match full-name city
            if not city_adcode:
                # full-name first, then short-name
                if select_city_adcode(adcode_map[(FULL_NAME, 'city')], year) or select_city_adcode(adcode_map[(SHORT_NAME, 'city')], year, short=True):
                    continue  # skip other matching if city is matched
            # match full-name county
            if not county_adcode:
                # full-name first, then short-name
                if select_county_adcode(adcode_map[(FULL_NAME, 'county')], year) or select_county_adcode(adcode_map[(SHORT_NAME, 'county')], year):
                    continue  # skip other matching if county is matched

        # modify city_adcode for special city
        if not province_adcode and city_adcode and not county_adcode:
            if self.adcode_to_location[(year,city_adcode)]['city_short'] == '朝阳':
                city_adcode = None


        return self.get_location_from_adcode(province_adcode, city_adcode, county_adcode, year)

    def parse_low_to_high(self, matched_results: List[dict], year: int = DEFAULT_YEAR) -> dict:
        """
        Low-to-high matching mode: match county first, then city, then province
        """
        province_adcode, city_adcode, county_adcode = None, None, None

        province_adcodes_full = set()
        city_adcodes_full = set()
        county_adcodes_full = set()
        province_adcodes_short = set()
        city_adcodes_short = set()
        county_adcodes_short = set()

        for each_match in matched_results:
            province_adcodes_full.update(each_match['adcode'][(FULL_NAME, 'province')])
            province_adcodes_short.update(each_match['adcode'][(SHORT_NAME, 'province')])
            city_adcodes_full.update(each_match['adcode'][(FULL_NAME, 'city')])
            if each_match['name'] not in ['朝阳']:
                city_adcodes_short.update(each_match['adcode'][(SHORT_NAME, 'city')])
            county_adcodes_full.update(each_match['adcode'][(FULL_NAME, 'county')])
            if each_match['name'] not in ['朝阳','荆州']:
                county_adcodes_short.update(each_match['adcode'][(SHORT_NAME, 'county')])

        def select_province_adcode(matched_adcodes):
            nonlocal province_adcode, city_adcode, county_adcode
            # select province adcode
            if len(matched_adcodes)==1:
                current_province_adcode = list(matched_adcodes)[0]
                # update final_match
                province_adcode = current_province_adcode
                return True
            return False
        def select_city_adcode(matched_adcodes, year):
            nonlocal province_adcode, city_adcode, county_adcode
            nonlocal province_adcodes_full, province_adcodes_short
            # select city adcode
            for each_city_adcode in matched_adcodes:
                location_infor = self.adcode_to_location[(year,each_city_adcode)]
                current_province_adcode = location_infor['province_adcode']
                # condition
                if_in_province_adcodes = (current_province_adcode in province_adcodes_full) or (current_province_adcode in province_adcodes_short)
                if_empty_province = (not province_adcodes_full) and (not province_adcodes_short)
                # update final_match
                if (if_in_province_adcodes) or (len(matched_adcodes)==1 and if_empty_province):
                    province_adcode = current_province_adcode
                    city_adcode = each_city_adcode
                    return True
            return False
        def select_county_adcode(matched_adcodes, year):
            nonlocal province_adcode, city_adcode, county_adcode
            nonlocal province_adcodes_full, province_adcodes_short, city_adcodes_full, city_adcodes_short
            for each_county_adcode in matched_adcodes:
                location_infor = self.adcode_to_location[(year,each_county_adcode)]
                current_province_adcode = location_infor['province_adcode']
                current_city_adcode = location_infor['city_adcode']
                # condition
                if_in_province_adcodes = (current_province_adcode in province_adcodes_full) or (current_province_adcode in province_adcodes_short)
                if_in_city_adcodes = (current_city_adcode in city_adcodes_full) or (current_city_adcode in city_adcodes_short)
                if_empty_province = (not province_adcodes_full) and (not province_adcodes_short)
                if_empty_city = (not city_adcodes_full) and (not city_adcodes_short)
                # update final_match
                if (if_in_province_adcodes and if_in_city_adcodes) or \
                   (if_in_city_adcodes) or \
                   (if_in_province_adcodes and each_county_adcode not in ['320106','320302']) \
                   or (if_empty_province and if_empty_city and len(matched_adcodes)==1 ):
                    province_adcode = current_province_adcode
                    city_adcode = current_city_adcode
                    county_adcode = each_county_adcode
                    return True
            return False
    
        # matching with full-name county
        if not county_adcode and len(county_adcodes_full)>0:
            select_county_adcode(county_adcodes_full, year)
        # matching with short-name county
        if not county_adcode and len(county_adcodes_short)>0:
            select_county_adcode(county_adcodes_short, year)
        # matching with full-name city
        if not city_adcode and len(city_adcodes_full)>0:
            select_city_adcode(city_adcodes_full, year)
        # matching with short-name city
        if not city_adcode and len(city_adcodes_short)>0:
            select_city_adcode(city_adcodes_short, year)
        # matching with full-name province
        if not province_adcode and len(province_adcodes_full)>0:
            select_province_adcode(province_adcodes_full)
        # matching with short-name province
        if not province_adcode and len(province_adcodes_short)>0:
            select_province_adcode(province_adcodes_short)

        return self.get_location_from_adcode(province_adcode, city_adcode, county_adcode, year)


    def parse_single(self, address: str, year: int = DEFAULT_YEAR, mode: int = LEFT_TO_RIGHT, drop: List[str] = None) -> dict:
        """
        Parse a single address string.
        """
        final_match = {
            'province_name': None, 'province_adcode': None, 'province_id': None,
            'city_name': None, 'city_adcode': None, 'city_id': None,
            'county_name': None, 'county_adcode': None, 'county_id': None 
        }

        # drop specified columns
        def drop_columns(final_match, drop):
            current_match = final_match.copy()
            if drop:
                for each_drop in drop:
                    if each_drop=='name':
                        current_match.pop('province_name')
                        current_match.pop('city_name')
                        current_match.pop('county_name')   
                    elif each_drop=='adcode':
                        current_match.pop('province_adcode')    
                        current_match.pop('city_adcode')
                        current_match.pop('county_adcode')
                    elif each_drop=='id':
                        current_match.pop('province_id')
                        current_match.pop('city_id')
                        current_match.pop('county_id')
            return current_match

        # empty address
        if not address.strip():
            return drop_columns(final_match, drop)

        # drop overlapping matches and get best matches
        matched_results = self.get_best_matches(address.strip(), year)
        
        # print(address)
        # print(matched_results)

        # parse address matches
        if mode==LEFT_TO_RIGHT:
            final_match = self.parse_left_to_right(matched_results, year)
        elif mode==LOW_TO_HIGH:
            final_match = self.parse_low_to_high(matched_results, year)
        else:
            raise ValueError(f"Unsupported matching mode: {mode}")

        return drop_columns(final_match, drop)
    
    def parse_batch(self, input_data: pd.DataFrame, mode: int = LEFT_TO_RIGHT, drop: List[str] = None, prefix: str = '', suffix: str = '', max_workers: int = 4) -> pd.DataFrame:
        """
        Parse a batch of addresses with associated years using multi-threading.
        Input DataFrame must have 'address' and 'year' columns.
        """

        # preparing for matching 
        match_year_list = input_data['year'].unique().tolist()
        self._build_automaton(match_year_list)

        # multi-threading parallel execution
        tasks = list(zip(input_data.index, input_data['address'], input_data['year']))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            parsed_results = list(executor.map(
                lambda task: self.parse_single(task[1], task[2], mode=mode, drop=drop),  # task[1]=address, task[2]=year
                tasks
            ))
        processed_dfs = pd.DataFrame(parsed_results, index=input_data.index)
        # drop specified columns
        if drop:
            for each_drop in drop:
                if each_drop=='address':
                    input_data.drop(columns=['address'], inplace=True)
                elif each_drop=='year':
                    input_data.drop(columns=['year'], inplace=True)
        # merge results with input data
        final_df = pd.concat([input_data, processed_dfs], axis=1) 

        # final order
        target_columns = [
            'address', 'year',  # original input columns
            'province_name', 'city_name', 'county_name',  # parsed names
            'province_adcode', 'city_adcode', 'county_adcode',  # parsed adcodes
            'province_id', 'city_id', 'county_id'  # parsed ids 
        ]
        valid_columns = [col for col in target_columns if col in final_df.columns]
        final_df = final_df[valid_columns]

        # add prefix and suffix to column names
        final_df.columns = [prefix + col + suffix for col in final_df.columns]

        return final_df




# --- Global Interface Functions ---
address_parser = AddressParser()

# interface function for Python
def getlocation(input_data: Union[str, List[str], pd.Series], 
                year: Union[int, List[int], pd.Series] = DEFAULT_YEAR, 
                mode: int = LEFT_TO_RIGHT, 
                drop: List[str] = None,
                prefix: str = '',
                suffix: str = '',
                max_workers: int = 4
                ) -> pd.DataFrame:
    """
    Address parser for Chinese administrative divisions. Get province, city, and county names, administrative division codes, and IDs from addresses.
        
    Args:
        input_data: Input addresses (required). Support str, list, np.ndarray, or pd.Series.
        year: Year for matching. Default is to load 2024 data. Valid range is from 1980 to 2024, and invalid years will be clipped to the default year 2024.
            - int: use the same year for all addresses
            - list of int, or pd.Series: use the corresponding year for each address
        mode: Matching mode. Default is 1.
            - 1: left to right (high to low, province to county), following string order
            - 2: low to high (county to province), ignoring string order; not recommended for basic use
        drop: Column list to drop in the final output. Default is None.
            - 'address': drop the raw address column
            - 'year': drop the year column
            - 'name': drop province_name, city_name, and county_name columns
            - 'adcode': drop province_adcode, city_adcode, and county_adcode columns
            - 'id': drop province_id, city_id, and county_id columns
        prefix: Prefix to add to column names.
        suffix: Suffix to add to column names.
        max_workers: Maximum number of worker threads. Default is 4.
    Returns:
        pd.DataFrame: columns with address (raw address), year (parsing year), province_name (province full name), city_name (city full name), county_name (county full name), province_adcode (province code), city_adcode (city administrative code), county_adcode(county administrative code), province_id (province ID), city_id (city ID), county_id (county ID)
            - Note: County-level IDs are currently **unreliable**! Province- and city-level IDs have been manually verified.

    Examples:
        Simple example:
        >>> import cnloc
        >>> result = cnloc.getlocation('江苏省昆山市千灯镇玉溪西路', year=2023)
        >>> print(result)
        
        Batch example:
        >>> import cnloc
        >>> address_data = ['江苏省昆山市千灯镇玉溪西路', '广东省深圳市南山区深南大道']
        >>> result = cnloc.getlocation(address_data, year=2023, mode=1)
        >>> print(result)
    """
    # uniform input to DataFrame, handle different input types
    if isinstance(input_data, (str, list, pd.Series)):
        df = pd.DataFrame({
            'address': input_data if isinstance(input_data, (list, pd.Series)) else [input_data],
            'year': year
        })
        # fill missing address
        df['address'] = df['address'].fillna("")
        # fill missing year
        df['year'] = df['year'].fillna(DEFAULT_YEAR).astype(int)
        # clip year to valid range
        df['year'] = df['year'].apply(lambda year: year if 1980 <= year <= DEFAULT_YEAR else DEFAULT_YEAR)
    else:
        raise TypeError("Only support str, list, np.ndarray, or pd.Series as input")
    
    return address_parser.parse_batch(df, mode=mode, drop=drop, prefix=prefix, suffix=suffix, max_workers=max_workers)


# interface function for Stata
def parse_address_from_Stata(input_data: str, year: str, drop: str = None, mode: int = 1, prefix: str = '', suffix: str = ''):
    from sfi import Data  # integrated in Stata
    # get data
    try:  # input year as int
        year = int(year)
        dataraw = Data.get([input_data])
        dataframe = pd.DataFrame(dataraw, columns=[input_data])
        dataframe[year] = year
    except ValueError as e:  # input year as variable name
        dataraw = Data.get([input_data, year])
        dataframe = pd.DataFrame(dataraw, columns=[input_data, year])
    # variables to drop, default is to drop address
    drop = drop.split() if drop else None
    drop = (drop + ['address']) if drop else ['address']
    # parse address
    final_location = getlocation(dataframe[input_data], year=dataframe[year], drop=drop, mode=mode, prefix=prefix, suffix=suffix)
	# fill missing value
    for each in ["province_name","city_name","county_name","province_adcode","city_adcode","county_adcode", "province_id", "city_id", "county_id"]:
        new_name = prefix+each+suffix
        if new_name in final_location.columns:
            final_location[new_name] = final_location[new_name].fillna('')
    # create variable format
    for col in final_location.columns:
        if pd.api.types.is_integer_dtype(final_location[col]):
            Data.addVarInt(col)
        elif pd.api.types.is_float_dtype(final_location[col]):
            Data.addVarDouble(col)
        elif pd.api.types.is_string_dtype(final_location[col]):
            max_length = final_location[col].str.len().max()
            Data.addVarStr(col, max_length)
    # python dataframe to stata
    for each_variable in final_location.columns:
        Data.store(each_variable, None,final_location[each_variable],None)


