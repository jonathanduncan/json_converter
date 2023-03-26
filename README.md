# json_converter
Little python script to take Google Map's location history dump files and converts them into filtered csv files

It looks for json files in its own folder.

The three categrories it filters for are: Date, Miles, and Address

It uses pathlib and vincenty
