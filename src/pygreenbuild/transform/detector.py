from .mappings import CWA_DAY_MAPPING, CWA_HOUR_MAPPING, CWA_MONTH_MAPPING


def detect_mapping(data):

    if not data:
        raise ValueError("資料為空")

    sample = data[0]

    if "DataTime" in sample:
        return CWA_HOUR_MAPPING

    elif "DataDate" in sample:
        return CWA_DAY_MAPPING

    elif "DataYearMonth" in sample:
        return CWA_MONTH_MAPPING

    else:
        raise ValueError("未知資料格式")
