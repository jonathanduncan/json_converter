import json
from pathlib import Path
from vincenty import vincenty

def main():
    json_files = {}
    for f in Path().cwd().iterdir():
        if f.suffix == '.json':

            json_files[f.stem] = f
            print(f.stem)

    if len(json_files) == 0:
        print("No json files found in current directory")
        return
    else:
        for filename, filepath in json_files.items():
            try:
                with open(filepath, "r", encoding="utf8") as f:
                    parsed_json = json.load(f)
            except OSError as error:
                print("Error opening input file %s: %s" % (filename, error))
                return
            except MemoryError:
                print("File too big")
                return

            items = parsed_json['timelineObjects']
            desired_items = list()
            trip = []
            skip = False
            trip_requirements = {'activitySegment': False, 'placeVisit': False}


            for i, cat in enumerate(items):
                # There are two types of timelineObjects, activitySegment and placeVisit
                # we need to look for activitySegment first, then placeVisit
                # if there is a placeVisit first, skip it and keep looking for activitySegment
                # if we have an activitySegment, and we find another activitySegment, replace the previous one with the new one and keep looking for placeVisit
                # when we have both activitySegment and placeVisit, we have a complete trip which we can add to the desired_items list

                # look for activitySegment first
                if cat.get('activitySegment', None) is not None:

                    # if the activitySegment type is not 'IN_PASSENGER_VEHICLE' or 'IN_VEHICLE', skip and skip looking for placeVisit
                    if cat['activitySegment']['activityType'] == 'IN_PASSENGER_VEHICLE' or \
                            cat['activitySegment']['activityType'] == 'IN_VEHICLE':

                        # if there is no parkingEvent, skip and skip looking for placeVisit
                        if cat['activitySegment'].get('parkingEvent', None) is None:
                            continue


                        timestamp = cat['activitySegment']['parkingEvent'].get('timestamp', None)
                        if timestamp is None:
                            trip_requirements['activitySegment'] = False
                            continue
                        date = str(timestamp.split('T')[0])

                        trip.append(date)

                        start_coord = (int(cat['activitySegment']['startLocation']['latitudeE7'])/1e7, int(cat['activitySegment']['startLocation']['longitudeE7'])/1e7)
                        end_coord = (int(cat['activitySegment']['endLocation']['latitudeE7'])/1e7, int(cat['activitySegment']['endLocation']['longitudeE7'])/1e7)
                        distance = vincenty(start_coord, end_coord, miles=True)
                        trip.append(str(distance))

                        trip_requirements['activitySegment'] = True

                # look for placeVisit
                if cat.get('placeVisit', None) is not None and trip_requirements['activitySegment']:
                    # if there is no place visit, skip
                    if cat.get('placeVisit', None) is None:
                        continue

                    messy_string = str(cat['placeVisit']['location'].get('address', None))
                    if messy_string is None:
                        trip.clear()
                        trip_requirements['activitySegment'] = False
                        continue
                    address = messy_string.replace(',', '')
                    trip.append(address)
                    desired_items.append(trip.copy())
                    trip.clear()

                    trip_requirements['activitySegment'] = False



                try:
                    with open(f'{filename}.csv', "w") as f:
                        f.write('Date,Distance,Address\n')
                        for trips in desired_items:
                            f.write(','.join(trips))
                            f.write('\n')
                except OSError as error:
                    print("Error creating output file for writing: %s" % error)
                    return


if __name__ == "__main__":
    main()
