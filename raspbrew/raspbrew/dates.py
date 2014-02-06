import datetime


def unix_time(dt):
	dt = dt.replace(tzinfo=None)
	epoch = datetime.datetime.utcfromtimestamp(0)
	delta = dt - epoch
	return delta.total_seconds()


def unix_time_millis(dt):
	return unix_time(dt) * 1000.0