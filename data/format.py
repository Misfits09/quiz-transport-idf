import csv, json

allowed_routes = [
    "1", "2", "3","3B", "4", "5", "6", "7", "7B", "8", "9", "10", "11", "12", "13", "14",
    "A", "B", "C", "D", "E", "H", "J", "K", "L", "N", "P", "R",
    "T1", "T2", "T3a", "T3b", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12", "T13", "T14",
]

routes = dict()

# Read traces-des-lignes-de-transport-en-commun-idfm.csv

data = open("./traces-des-lignes-de-transport-en-commun-idfm.csv", "r")
csv_reader = csv.reader(data, delimiter=";")
csv_reader.__next__() # Skip first line

for line in csv_reader:
    if line[3] not in [
        "Tram", "Subway", "Rail"
    ] or line[1] in [
        "TER",
        "ORLYVAL",
        "CDG VAL"
    ]: continue

    if line[1] not in allowed_routes: print("WARN: Route %s not allowed" % line[1])

    routes[line[0]] = {
        "name": line[1],
        "type": line[3],
        "color": line[4],
        "stops": {},
        "shape": {
            "coordinates": [],
            "type": "MultiLineString",
        }
    }


data = open("./traces-du-reseau-ferre-idf.csv", "r")
csv_reader = csv.reader(data, delimiter=";")
csv_reader.__next__() # Skip first line

for line in csv_reader:
    if "IDFM:" + line[3] not in routes: continue

    segment_data = json.loads(line[1])
    if segment_data["type"] != "LineString":
        print("ERROR: Segment %s is not a LineString" % line[0])
        exit(1)

    routes["IDFM:" + line[3]]["shape"]["coordinates"].append(segment_data["coordinates"])
    routes["IDFM:" + line[3]]["logo"] = line[-1]

data = open("./arrets-lignes.csv", "r")

# Read csv file
csv_reader = csv.reader(data, delimiter=";")
csv_reader.__next__() # Skip first line

for line in csv_reader:
    if line[0] in routes:
        # if line[5] in routes[line[0]]["stops"]:
        #     print("WARN: Duplicate stop %s for route %s" % (line[5], line[1]))

        routes[line[0]]["stops"][line[5]] = dict({
            "id": line[4],
            "coords": (line[6], line[7])
        })

stops_routes = dict()
for route in routes:
    for stop in routes[route]["stops"]:
        if stop in stops_routes:
            stops_routes[stop]["routes"].append(route)
        else:
            stops_routes[stop] = {
                "coords": routes[route]["stops"][stop]["coords"],
                "id": routes[route]["stops"][stop]["id"],
                "routes": [route],
            }

with open("../app/stops.json", "w") as f:
    f.write(json.dumps(stops_routes))

for route in routes:
    routes[route]["stops"] = [
        routes[route]["stops"][stop]["id"] for stop in routes[route]["stops"]
    ]

# Write to file
with open("../app/routes.json", "w") as f:
    f.write(json.dumps(routes))
    print("Lignes:")
    for route_name in sorted(routes[route]["name"] for route in routes):
        print(" - %s" % route_name)

