"""
cnloc
中国行政区划地址解析器
Address Parser for Chinese Administrative Divisions
"""

# V0.2.1 (2026-11-20): support county_id; add 2025 data; change data source and correct data errors
# V0.1.7 (2026-01-13)


__version__ = "0.2.1"

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
DEFAULT_YEAR = 2025  # default year for address parsing
LEFT_TO_RIGHT, LOW_TO_HIGH = 1, 2  # matching modes: left-to-right, low-to-high

LEVEL_PREFIX = {RANK_PROVINCE: 'province', RANK_CITY: 'city', RANK_COUNTY: 'county'}



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
            self.global_automaton: Optional[ahocorasick.Automaton] = None
            self.adcode_to_location: Dict[str, List[dict]] = {}
            self._load_data()
            self._build_automaton()
            AddressParser._initialized = True

    def _load_data(self) -> None:
        path = files("cnloc.data").joinpath("location_20261001.csv")
        with path.open(newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            rank = int(row['rank'])
            me = LEVEL_PREFIX[rank]
            adcode = row[f'{me}_adcode']
            entry = {
                'adcode': adcode, 'rank': rank,
                'year_begin': int(row['year_begin']), 'year_end': int(row['year_end']),
                'province_name': row['province_name'] or None,
                'city_name': row['city_name'] or None,
                'county_name': row['county_name'] or None,
                'province_adcode': row['province_adcode'] or None,
                'city_adcode': row['city_adcode'] or None,
                'county_adcode': row['county_adcode'] or None,
                'province_id': row['province_id'] or None,
                'city_id': row['city_id'] or None,
                'county_id': row['county_id'] or None,
                'province_name_short': row['province_name_short'] or None,
                'city_name_short': row['city_name_short'] or None,
                'county_name_short': row['county_name_short'] or None,
            }
            self.adcode_to_location.setdefault(adcode, []).append(entry)

    def _build_automaton(self) -> None:
        # structure: name -> {(mode, rank_str): [(adcode, province_adcode, city_adcode, county_adcode, year_begin, year_end)]}
        skip_names = {'市辖区', '县', '市', '省直辖县级行政区划', '自治区直辖县级行政区划'}
        name_to_adcode_map: Dict[str, dict] = defaultdict(lambda: {
            (FULL_NAME, RANK_PROVINCE): [], (SHORT_NAME, RANK_PROVINCE): [],
            (FULL_NAME, RANK_CITY): [], (SHORT_NAME, RANK_CITY): [],
            (FULL_NAME, RANK_COUNTY): [], (SHORT_NAME, RANK_COUNTY): [],
        })

        for adcode, entries in self.adcode_to_location.items():
            for entry in entries:
                rank = entry['rank']
                me = LEVEL_PREFIX[rank]
                name = entry[f'{me}_name']
                name_short = entry[f'{me}_name_short']
                year_begin = entry['year_begin']
                year_end = entry['year_end']

                if name in skip_names:
                    continue

                tuple_base = (adcode, entry['province_adcode'], entry['city_adcode'], entry['county_adcode'], year_begin, year_end)
                if name:
                    name_to_adcode_map[name][(FULL_NAME, rank)].append(tuple_base)
                if name_short and name_short != name and name_short not in skip_names:
                    name_to_adcode_map[name_short][(SHORT_NAME, rank)].append(tuple_base)

        # build automaton
        automaton = ahocorasick.Automaton()
        for name, adcode_map in name_to_adcode_map.items():
            automaton.add_word(name, {'name': name, 'adcode_map': adcode_map})
        automaton.make_automaton()
        self.global_automaton = automaton

    def get_best_matches(self, sentence: str, year: int = DEFAULT_YEAR, county_short: bool = False) -> List[dict]:
        """
        Get best matches, keeping longest and non-overlapping matches
        """
        matches = []
        for end_idx, content in self.global_automaton.iter(sentence):
            adcode_map = {k: [] for k in content['adcode_map']}
            has_valid = False
            for (name_type, rank), tuples in content['adcode_map'].items():
                # skip county short name if not requested
                if not county_short and rank == RANK_COUNTY and name_type == SHORT_NAME:
                    continue
                # filter valid tuples based on year
                for t in tuples:
                    if t[4] <= year <= t[5]:
                        adcode_map[(name_type, rank)].append(t)
                        has_valid = True
            if not has_valid:
                continue
            length = len(content['name'])
            start_idx = end_idx - length + 1
            matches.append((start_idx, end_idx, length, content['name'], adcode_map))

        # sort by start index ascending, length descending (prefer longer matches at the same start)
        matches.sort(key=lambda x: (x[0], -x[2]))

        # filter out overlapping matches
        best_matches = []
        last_end = -1
        for start_idx, end_idx, length, name, adcode_map in matches:
            if start_idx > last_end:
                best_matches.append({"name": name, "adcode_map": adcode_map})
                last_end = end_idx

        return best_matches

    def get_location_from_adcode(self, province_adcode: str, city_adcode: str = None, county_adcode: str = None, year: int = DEFAULT_YEAR) -> dict:
        start_adcode = county_adcode or city_adcode or province_adcode
        result = {
            'province_name': None, 'province_adcode': None, 'province_id': None,
            'city_name': None, 'city_adcode': None, 'city_id': None,
            'county_name': None, 'county_adcode': None, 'county_id': None,
        }
        if not start_adcode:
            return result
        for e in self.adcode_to_location.get(start_adcode, []):
            if e['year_begin'] <= year <= e['year_end']:
                result['province_name'] = e.get('province_name')
                result['province_adcode'] = e['province_adcode']
                result['province_id'] = e.get('province_id')
                result['city_name'] = e.get('city_name')
                result['city_adcode'] = e['city_adcode']
                result['city_id'] = e.get('city_id')
                result['county_name'] = e.get('county_name')
                result['county_adcode'] = e['county_adcode']
                result['county_id'] = e.get('county_id')
                break
        return result

    def parse_left_to_right(self, matched_results: List[dict], year: int = DEFAULT_YEAR) -> dict:
        province_adcode, city_adcode, county_adcode = None, None, None

        def select_province_adcode(matched_adcodes):
            nonlocal province_adcode
            for _, current_province_adcode, *_ in matched_adcodes:
                if current_province_adcode:
                    # update location information
                    province_adcode = current_province_adcode
                    return True
            return False

        def select_city_adcode(matched_adcodes, short=False):
            nonlocal province_adcode, city_adcode
            for _, current_province_adcode, current_city_adcode, *_ in matched_adcodes:
                if current_city_adcode:
                    # special: city_name_short=='朝阳' and no province context, lock city first
                    if short and current_city_adcode in ('212200', '211300') and not province_adcode:
                        city_adcode = current_city_adcode
                        return True
                    # update location information
                    if (province_adcode == current_province_adcode) or (not province_adcode):
                        province_adcode = current_province_adcode
                        city_adcode = current_city_adcode
                        return True
            return False

        def select_county_adcode(matched_adcodes):
            nonlocal province_adcode, city_adcode, county_adcode
            for _, current_province_adcode, current_city_adcode, current_county_adcode, *_ in matched_adcodes:
                if current_county_adcode:
                    # update location information: 江苏省南京市鼓楼区(320106), 江苏省徐州市鼓楼区(320302)
                    if (province_adcode == current_province_adcode and city_adcode == current_city_adcode) or \
                       (province_adcode == current_province_adcode and not city_adcode and current_county_adcode not in ('320106', '320302')) or \
                       (not province_adcode and city_adcode == current_city_adcode) or \
                       (not province_adcode and not city_adcode and len(matched_adcodes) == 1):
                        province_adcode = current_province_adcode
                        city_adcode = current_city_adcode
                        county_adcode = current_county_adcode
                        return True
            return False

        # matching from left to right
        for each_match in matched_results:
            adcode_map = each_match['adcode_map']
            # match province
            if not province_adcode:
                if select_province_adcode(adcode_map[(FULL_NAME, RANK_PROVINCE)]):
                    continue
                if select_province_adcode(adcode_map[(SHORT_NAME, RANK_PROVINCE)]):
                    continue
            # match city
            if not city_adcode:
                if select_city_adcode(adcode_map[(FULL_NAME, RANK_CITY)]):
                    continue
                if select_city_adcode(adcode_map[(SHORT_NAME, RANK_CITY)], short=True):
                    continue
            # match county
            if not county_adcode:
                if select_county_adcode(adcode_map[(FULL_NAME, RANK_COUNTY)]):
                    continue
                if select_county_adcode(adcode_map[(SHORT_NAME, RANK_COUNTY)]):
                    continue

        # modify city_adcode for special city: only city='朝阳' matched but no province context
        if not province_adcode and city_adcode and not county_adcode:
            if city_adcode in ('212200', '211300'):
                city_adcode = None

        return self.get_location_from_adcode(province_adcode, city_adcode, county_adcode, year)

    def parse_low_to_high(self, matched_results: List[dict], year: int = DEFAULT_YEAR) -> dict:
        province_adcode, city_adcode, county_adcode = None, None, None

        province_adcodes_full = set()
        city_adcodes_full = set()
        county_adcodes_full = set()
        province_adcodes_short = set()
        city_adcodes_short = set()
        county_adcodes_short = set()

        for each_match in matched_results:
            adcode_map = each_match['adcode_map']

            province_adcodes_full.update(adcode_map[(FULL_NAME, RANK_PROVINCE)])
            province_adcodes_short.update(adcode_map[(SHORT_NAME, RANK_PROVINCE)])
            city_adcodes_full.update(adcode_map[(FULL_NAME, RANK_CITY)])
            # '朝阳' is a special case
            city_short_filtered = {t for t in adcode_map[(SHORT_NAME, RANK_CITY)] if t[2] not in {'212200', '211300'}}
            city_adcodes_short.update(city_short_filtered)
            county_adcodes_full.update(adcode_map[(FULL_NAME, RANK_COUNTY)])
            # '朝阳' and '荆州' are special cases
            county_short_filtered = {t for t in adcode_map[(SHORT_NAME, RANK_COUNTY)] if t[3] not in {'211221', '212201', '421003'}}
            county_adcodes_short.update(county_short_filtered)

        def select_province_adcode(matched_adcodes):
            nonlocal province_adcode, city_adcode, county_adcode
            if len(matched_adcodes) == 1:
                _, current_province_adcode, *_ = list(matched_adcodes)[0]
                province_adcode = current_province_adcode
                return True
            return False

        def select_city_adcode(matched_adcodes):
            nonlocal province_adcode, city_adcode, county_adcode
            nonlocal province_adcodes_full, province_adcodes_short
            prov_set_full = {t[1] for t in province_adcodes_full}
            prov_set_short = {t[1] for t in province_adcodes_short}
            for _, current_province_adcode, current_city_adcode, *_ in matched_adcodes:
                if current_province_adcode in prov_set_full or current_province_adcode in prov_set_short:
                    province_adcode = current_province_adcode
                    city_adcode = current_city_adcode
                    return True
                if len(matched_adcodes) == 1 and not prov_set_full and not prov_set_short:
                    province_adcode = current_province_adcode
                    city_adcode = current_city_adcode
                    return True
            return False

        def select_county_adcode(matched_adcodes):
            nonlocal province_adcode, city_adcode, county_adcode
            nonlocal province_adcodes_full, province_adcodes_short, city_adcodes_full, city_adcodes_short
            prov_set_full = {t[1] for t in province_adcodes_full}
            prov_set_short = {t[1] for t in province_adcodes_short}
            city_set_full = {t[2] for t in city_adcodes_full}
            city_set_short = {t[2] for t in city_adcodes_short}
            for _, current_province_adcode, current_city_adcode, current_county_adcode, *_ in matched_adcodes:
                if_in_province = current_province_adcode in prov_set_full or current_province_adcode in prov_set_short
                if_in_city = current_city_adcode in city_set_full or current_city_adcode in city_set_short
                if_empty_province = not prov_set_full and not prov_set_short
                if_empty_city = not city_set_full and not city_set_short
                # update location information: 江苏省南京市鼓楼区(320106), 江苏省徐州市鼓楼区(320302)
                if (if_in_province and if_in_city) or \
                   (if_in_city) or \
                   (if_in_province and current_county_adcode not in ('320106', '320302')) \
                   or (if_empty_province and if_empty_city and len(matched_adcodes) == 1):
                    province_adcode = current_province_adcode
                    city_adcode = current_city_adcode
                    county_adcode = current_county_adcode
                    return True
            return False

        if not county_adcode and len(county_adcodes_full) > 0:
            select_county_adcode(county_adcodes_full)
        if not county_adcode and len(county_adcodes_short) > 0:
            select_county_adcode(county_adcodes_short)
        if not city_adcode and len(city_adcodes_full) > 0:
            select_city_adcode(city_adcodes_full)
        if not city_adcode and len(city_adcodes_short) > 0:
            select_city_adcode(city_adcodes_short)
        if not province_adcode and len(province_adcodes_full) > 0:
            select_province_adcode(province_adcodes_full)
        if not province_adcode and len(province_adcodes_short) > 0:
            select_province_adcode(province_adcodes_short)

        return self.get_location_from_adcode(province_adcode, city_adcode, county_adcode, year)

    def parse_single(self, address: str, year: int = DEFAULT_YEAR, mode: int = LEFT_TO_RIGHT, drop: List[str] = None, county_short: bool = False) -> dict:
        """Parse a single address string, returning a province/city/county dict optionally filtered by drop."""
        if not address.strip():
            final_match = self.get_location_from_adcode(None, None, None, year)
        else:
            matched_results = self.get_best_matches(address.strip(), year, county_short)

            if mode == LEFT_TO_RIGHT:
                final_match = self.parse_left_to_right(matched_results, year)
            elif mode == LOW_TO_HIGH:
                final_match = self.parse_low_to_high(matched_results, year)
            else:
                raise ValueError(f"Unsupported matching mode: {mode}")

        if drop:
            for each_drop in drop:
                if each_drop == 'name':
                    final_match.pop('province_name', None); final_match.pop('city_name', None); final_match.pop('county_name', None)
                elif each_drop == 'adcode':
                    final_match.pop('province_adcode', None); final_match.pop('city_adcode', None); final_match.pop('county_adcode', None)
                elif each_drop == 'id':
                    final_match.pop('province_id', None); final_match.pop('city_id', None); final_match.pop('county_id', None)
        return final_match

    def parse_batch(self, input_data: pd.DataFrame, mode: int = LEFT_TO_RIGHT, drop: List[str] = None, prefix: str = '', suffix: str = '', county_short: bool = False, max_workers: int = 4) -> pd.DataFrame:
        """
        Parse a batch of addresses with associated years using multi-threading.
        Input DataFrame must have 'address' and 'year' columns.
        """

        tasks = list(zip(input_data.index, input_data['address'], input_data['year']))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            parsed_results = list(executor.map(
                lambda task: self.parse_single(task[1], task[2], mode=mode, drop=drop, county_short=county_short),
                tasks
            ))
        processed_dfs = pd.DataFrame(parsed_results, index=input_data.index)

        if drop:
            for each_drop in drop:
                if each_drop in ('address', 'year'):
                    input_data = input_data.drop(columns=[each_drop])

        final_df = pd.concat([input_data, processed_dfs], axis=1)

        target_columns = [
            'address', 'year',
            'province_name', 'city_name', 'county_name',
            'province_adcode', 'city_adcode', 'county_adcode',
            'province_id', 'city_id', 'county_id'
        ]
        valid_columns = [col for col in target_columns if col in final_df.columns]
        final_df = final_df[valid_columns]

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
                county_short: bool = False,
                max_workers: int = 4
                ) -> pd.DataFrame:
    """
    Address parser for Chinese administrative divisions. Get province, city, and county names, administrative division codes, and IDs from addresses.
        
    Args:
        input_data: Input addresses (required). Support str, list, np.ndarray, or pd.Series.
        year: Year for matching. Default is to load 2025 data. Valid range is from 1980 to 2025, and invalid years will be clipped to the default year 2025.
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
        county_short: Whether to consider short names for county-level matching. Default is False.
        max_workers: Maximum number of worker threads. Default is 4.
    Returns:
        pd.DataFrame: columns with address (raw address), year (parsing year), province_name (province full name), city_name (city full name), county_name (county full name), province_adcode (province code), city_adcode (city administrative code), county_adcode(county administrative code), province_id (province ID), city_id (city ID), county_id (county ID)
            - Note: County-level IDs are currently **unreliable**! Province- and city-level IDs have been manually verified.

    Examples:
        Simple example:
        >>> import cnloc
        >>> result = cnloc.getlocation('江苏省昆山市千灯镇玉溪西路')
        >>> print(result)
        
        Batch example:
        >>> import cnloc
        >>> address_data = ['江苏省昆山市千灯镇玉溪西路', '广东省深圳市南山区深南大道']
        >>> result = cnloc.getlocation(address_data, year=2023, mode=1, county_short=True)
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
    
    return address_parser.parse_batch(df, mode=mode, drop=drop, prefix=prefix, suffix=suffix, county_short=county_short, max_workers=max_workers)


# interface function for Stata
def parse_address_from_Stata(input_data: str, year: str, drop: str = None, mode: int = 1, prefix: str = '', suffix: str = '', sample: str = None, county_short: bool = False):
    from sfi import Data  # integrated in Stata
    # get data
    try:  # input year as int
        year = int(year)
        dataraw = Data.get([input_data], selectvar=sample)
        dataframe = pd.DataFrame(dataraw, columns=[input_data])
        dataframe['year'] = year
        dataframe.rename(columns={input_data: 'input_data'}, inplace=True)
    except ValueError as e:  # input year as variable name
        dataraw = Data.get([input_data, year], selectvar=sample)
        dataframe = pd.DataFrame(dataraw, columns=[input_data, year])
        dataframe.rename(columns={input_data: 'input_data', year: 'year'}, inplace=True)
    # variables to drop, default is to drop address
    drop = drop.split() if drop else None
    drop = (drop + ['address']) if drop else ['address']
    # parse address
    final_location = getlocation(dataframe['input_data'], year=dataframe['year'], drop=drop, mode=mode, prefix=prefix, suffix=suffix, county_short=county_short)
    # fill missing value
    for each in ["province_name", "city_name", "county_name", "province_adcode", "city_adcode", "county_adcode", "province_id", "city_id", "county_id"]:
        new_name = prefix + each + suffix
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
            # if empty matching, set length to 1
            max_length = max(max_length, 1)
            Data.addVarStr(col, max_length)
    # python dataframe to stata
    for each_variable in final_location.columns:
        Data.store(each_variable, None, final_location[each_variable], selectvar=sample)