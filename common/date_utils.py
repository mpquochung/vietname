from datetime import date, timedelta, datetime
from pytz import timezone

DAY_IN_SECONDS = 24 * 60 * 60


def yesterday():
    """
    Return yesterday date in yyyy-mm-dd format
    """
    return day_ago(days=1)


def get_second_stamp():
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def get_minute_stamp():
    return datetime.now().strftime("%Y-%m-%d_%H%M")


def get_hour_stamp():
    return datetime.now().strftime("%Y-%m-%d_%H")


def get_date_stamp():
    return datetime.now().strftime("%Y-%m-%d")


def day_ago(days=1):
    """
    Return some days ago in yyyy-mm-dd format
    """
    d = date.today() - timedelta(days=days)
    return d.strftime('%Y-%m-%d')


def epoch_to_iso(seconds_since_epoch):
    return datetime.utcfromtimestamp(seconds_since_epoch).isoformat()


def epoch_to_basic_date_time(seconds_since_epoch):
    return datetime.utcfromtimestamp(seconds_since_epoch).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def iso_timestamp():
    return datetime.now().isoformat()


def basic_date_time(dt=None):
    """A basic formatter that combines a basic date and time, separated by a T: yyyyMMdd'T'HHmmss.SSSZ."""
    if dt is None:
        now = datetime.now()
    else:
        now = dt
    return now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def get_time_range(days_before):
    """
    Returns a time range by means of two values in milliseconds for a given number of days back.
    :param days_before: arbitrary number, the test is about to check that the fresh news are coming
    :return: days before in milliseconds, now in milliseconds
    """
    now_in_milliseconds = int(datetime.now().strftime("%s"))
    days_before_in_milliseconds = int((datetime.today() - timedelta(days=days_before)).strftime("%s"))
    return days_before_in_milliseconds, now_in_milliseconds


def convert_rss_to_basic_timestamp(timestamp):
    """
    Example: 'Mon, 02 Nov 2020 11:00:00 +0700' => 2020-11-02T16:00:00.000Z
    """
    datetime_object = datetime.strptime(timestamp, '%a, %d %b %Y %H:%M:%S %z')
    return epoch_to_basic_date_time(datetime_object.timestamp())


def convert_vietnam_timestamp_to_basic_timestamp(timestamp):
    """
    Example: 1/20/2021 4:09:13 PM => 2021-01-20T14:59:22.000Z
    """
    vietnam_tz = timezone('Asia/Ho_Chi_Minh')
    try:
        datetime_object = datetime.strptime(timestamp, '%m/%d/%Y %H:%M:%S')
    except ValueError:
        datetime_object = datetime.strptime(timestamp, '%m/%d/%Y %H:%M:%S %p')
    loc_dt = vietnam_tz.localize(datetime_object)
    return epoch_to_basic_date_time(loc_dt.timestamp())


def get_datetime_from_str(datetime_string, pattern='%Y-%m-%dT%H:%M:%S'):
    return datetime.strptime(datetime_string, pattern)


def get_datetime_from_basic(datetime_string, pattern='%Y-%m-%dT%H:%M:%S.%fZ'):
    return datetime.strptime(datetime_string, pattern)
