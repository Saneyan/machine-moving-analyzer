# Machine Tracking Analyzer

Analyzing by tracking data of cars, robots and another moving.

## What's this?

This analyzer analyzes whether the target object has been moivg or stopping during each time period and determines its position as (X, Y) point. At least more than 2 hours the target moves, the tracking point is ('no answer', 'no answer').

For the following data:

```csv
ONDate,ONTime,OFFDate,OFFTime,endX,endY
11/18/2013,10:25:31,11/28/2013,10:49:28,137.1599517,35.087345
11/18/2013,11:52:01,11/28/2013,11:59:32,137.18894,35.05638167
11/18/2013,12:37:44,11/18/2013,14:21:02,137.1628917,35.053795
```

It should be:

```csv
date,time,endX,endY
11/18/2013,10:00:00,137.1599517,35.087345
11/18/2013,11:00:00,137.18894,35.05638167
11/18/2013,12:00:00,137.18894,35.05638167
11/18/2013,13:00:00,no answer,no answer
11/18/2013,14:00:00,137.1628917,35.053795
```

This analyzer calculates each periods from timestamp based on the algorithm:

```
If a machine have been moving in the following time:
00:01 (1s) |----------*====*-------| 01:00 (3600s)
      		      ^
	           [target]

[target]: 00:30 (1800s)
==> To calculate begin time: [start] = [target] - [target] % 3600 + 1
==> To calculate end time: [end] = [start] + 3599
```

## Usage

```
python analyze.py <format> <csv_filename>
```

The `<format>` can be `id` for each ID, `date` for each date and `all` for all data. `<csv_filename>` must contains .csv extension.

The input file must be CSV file containing 'ONDate', 'ONTime', 'OFFDate', 'OFFTime', 'endX' and 'endY' header and the data. This script outputs results as a CSV file containing 'date', 'time', 'endX' and 'endY' header and the data.

## License

MIT License
