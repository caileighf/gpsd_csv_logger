import matplotlib.pyplot as plt
import datetime

import cartopy.crs as ccrs
import cartopy.feature as cf

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('-p', '--projection', type=str, 
                                              default='Mercator', 
                                              help="cartopy.crs.<proj> pass the case-sensitive cartopy Projection")
    parser.add_argument('--utm-zone', type=str, 
                                      default=None, 
                                      help="utm zone if UTM passed for -p/--projection")
    parser.add_argument('--feature', type=str,
                                     default=None,
                                     nargs='*')
    parser.add_argument('--track-dir', type=str,
                                       default=None)
    parser.add_argument('--csv-row-regex', type=str,
                                           default='')
    parser.add_argument('--csv-dt-strfmt', type=str,
                                           default=None)
    parser.add_argument('--csv-header-rows', type=int,
                                             default=0)
    parser.add_argument('--csv-columns', type=str,
                                         default=['lat', 'lon', 'time'],
                                         nargs=3,
                                         help="if the csv has the columns in a different order. Still needs to be the same names")
    parser.add_argument('-b', '--base', action="store_true", help="Plot base features (COASTLINE, OCEAN)")
    parser.add_argument('--no-gridlines', action="store_true", help="Plot without gridlines")
    parser.add_argument('-d', '--debug', action="store_true", help="Print debug messages")
    parser.add_argument('-f', '--fullscreen', action="store_true", help="Print debug messages")
    args = parser.parse_args()

    if args.fullscreen:
        mng = plt.get_current_fig_manager()
        backend = plt.get_backend()
        if args.debug: print(f'Current back-end: {backend}')

        if backend == 'TkAgg':
            mng.full_screen_toggle()
        elif backend == 'wxAgg':
            mng.frame.Maximize(True)
        elif backend == 'Qt4Agg':
            mng.window.showMaximized()
    else:
        from matplotlib.pyplot import figure
        figure(figsize=(8, 6), dpi=122)


    if args.projection != 'UTM':
        projection = getattr(ccrs, args.projection)
        ax = plt.axes(projection=projection())
    else:
        ax = plt.axes(projection=ccrs.UTM(zone=args.utm_zone))

    if args.base:
        args.feature = set.union(set(args.feature), set(['OCEAN', 'COASTLINE']))

    if args.debug:
        print(f'-----gpsd-csv-logger-plotter--------------------------')
        print(f'- Features to overlay:...{args.feature}')
        print(f'- Projection used:.......cartopy.crs.{args.projection}')
        print(f'------------------------------------------------------')

    if args.feature:
        for FEATURE in args.feature:
            ax.add_feature(getattr(cf, FEATURE))

    # Plot lat/lon point in passed csv
    if args.track_dir:
        columns = [], [], []

        import pathlib

        if args.track_dir[-1] != '/':
            # not a directory, user wants to only plot this file
            tracks = [pathlib.Path(args.track_dir)]
        else:
            tracks = sorted(pathlib.Path(args.track_dir).glob('track*.nmea'))

        import re
        csv_row_pattern = re.compile(args.csv_row_regex)

        for track in tracks:
            with open(track) as f:
                # loop through rows and create single track
                for row in f.readlines()[args.csv_header_rows:]:
                    # if user passed a regex string use that to expand the row
                    if args.csv_row_regex != '':
                        match = csv_row_pattern.match()
                        if match:
                            tokens = match.groups()
                            [columns[i].append(tokens[i]) for i in range(3)]
                    # otherwise assume 3 tokens comma delimited...
                    else:
                        tokens = row.strip().split(',')
                        [columns[i].append(tokens[i]) for i in range(3)]

        times = columns[args.csv_columns.index('time')]

        if args.csv_dt_strfmt:
            # turn into datetime objects if user passed a dt string format
            times = [datetime.datetime.strptime(t, args.csv_dt_strfmt) for t in times]
        else:
            times = [float(t) for t in times]

        lats = [float(l) for l in columns[args.csv_columns.index('lat')]]
        lons = [float(l) for l in columns[args.csv_columns.index('lon')]]

        if args.projection == 'UTM':
            # convert lat/lons to northing/easting
            import utm
            northing, easting, ts = [], [], []
            for lat, lon, t in zip(lats, lons, times):
                n, e, _, _ = utm.from_latlon(lat, lon)
                northing.append(n)
                easting.append(e)
                ts.append(t)

            ax.scatter(northing, easting, c=ts, cmap='jet', label='track in UTM Northing, Easting from lat/lon')
        else:
            ax.scatter(lats, lons, c=times, cmap='jet', label='track lat/lon in decimal degrees')

        ax.legend() # if we plotted a track

    if not args.no_gridlines:
        ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)

    ax.set_title('{} cartopy.crs.{}'.format(datetime.datetime.now(), args.projection))

    if args.debug:
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        offset = 2
        print('x limits: {},\ny limits: {},\noffset deg lat/lon: {}'.format(xlim, ylim, offset))
        ax.set_xlim((xlim[0] - offset, xlim[1] + offset))
        ax.set_ylim((ylim[0] - offset, ylim[1] + offset))

    plt.show()