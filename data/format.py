import csv, json, math

allowed_routes = [
    "1", "2", "3","3B", "4", "5", "6", "7", "7B", "8", "9", "10", "11", "12", "13", "14",
    "A", "B", "C", "D", "E", "H", "J", "K", "L", "N", "P", "R", "U",
    "T1", "T2", "T3a", "T3b", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12", "T13", "T14",
]

routes = dict()

# Read traces-des-lignes-de-transport-en-commun-idfm.csv
# Creates all routes with their name, type, color

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
        "stops": set(),
        "shape": {
            "coordinates": [],
            "type": "MultiLineString",
        }
    }

# Fix routes shape from traces-du-reseau-ferre-idf.csv

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

# Add stops to routes from arrets-lignes.csv

data = open("./arrets-lignes.csv", "r")
csv_reader = csv.reader(data, delimiter=";")
csv_reader.__next__() # Skip first line

stops = dict()

def distance(point1, point2):
    return ((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)**0.5

def project_point(point, segment):
    # calculate the vector representing the line segment
    segment_vector = (segment[1][0] - segment[0][0], segment[1][1] - segment[0][1])
    # calculate the vector representing the point's position relative to the start of the segment
    point_vector = (point[0] - segment[0][0], point[1] - segment[0][1])
    # calculate the dot product of the two vectors
    dot_product = point_vector[0] * segment_vector[0] + point_vector[1] * segment_vector[1]
    # calculate the length of the segment squared
    segment_length_squared = segment_vector[0] ** 2 + segment_vector[1] ** 2
    # calculate the projection of the point onto the line segment
    projection = (segment[0][0] + (dot_product * segment_vector[0]) / segment_length_squared,
                  segment[0][1] + (dot_product * segment_vector[1]) / segment_length_squared)
    return projection

def project(_point, route_id):
    point = (float(_point[0]), float(_point[1]))
    shape = routes[route_id]["shape"]["coordinates"]
    min_dist = math.inf
    pos = point
    for line in shape:
        if len(line) < 2:
            if distance(point, line[0]) < min_dist:
                min_dist = distance(point, line[0])
                pos = line[0]
            continue
        for i in range(1,len(line)):
            projected = project_point(point, (line[i-1], line[i]))
            if projected[0] < min(line[i-1][0], line[i][0]) or projected[0] > max(line[i-1][0], line[i][0]):
                end = line[i-1] if distance(point, line[i-1]) < distance(point, line[i]) else line[i]
                projected = (end[0], end[1])
                # print(projected)
            dist = distance(point, projected)
            if dist < min_dist:
                min_dist = dist
                pos = projected
    
    return pos


for line in csv_reader:
    if line[0] in routes:
        if line[5] in stops:
            if line[0] not in stops[line[5]]["routes"]:
                point = project((line[6], line[7]), line[0])
                stops[line[5]]["coords"].add((point[0], point[1], routes[line[0]]["color"]))
                stops[line[5]]["routes"].add(line[0])
        else:
            point = project((line[6], line[7]), line[0])
            stops[line[5]] = {
                "coords": set([(point[0], point[1], routes[line[0]]["color"])]),
                "id": line[4],
                "routes": set([line[0]]),
            }
        
        routes[line[0]]["stops"].add(stops[line[5]]["id"])

# Convert sets to lists for JSON serialization
for route in routes:
    routes[route]["stops"] = list(routes[route]["stops"])
for stop in stops:
    stops[stop]["coords"] = list(stops[stop]["coords"])
    stops[stop]["routes"] = list(stops[stop]["routes"])

# Write to files
with open("../app/stops.json", "w") as f:
    f.write(json.dumps(stops))

with open("../app/routes.json", "w") as f:
    f.write(json.dumps(routes))
    
    print("Lignes:")
    for route_name in sorted(routes[route]["name"] for route in routes):
        print(" - %s" % route_name)

# Generate all dots images

from PIL import Image

# Open the image
image = Image.open("../public/dot.png")

# Delete ../public/dots/*
import os

# Create the directory if it doesn't exist
if not os.path.exists("../public/dots"):
    os.makedirs("../public/dots")
else: 
    for file in os.listdir("../public/dots"):
        os.remove("../public/dots/" + file)

# Convert the image to RGB mode if it's in indexed mode
if image.mode == "P":
    image = image.convert("RGB")

for color in set(x["color"] for x in routes.values()):
    # Get the pixel data
    _image = image.copy()
    pixels = _image.load()

    # Hex color to rgb values
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)

    # Replace white pixels with green
    for x in range(image.width):
        for y in range(image.height):
            if pixels[x, y] == (255, 255, 255, 255):
                pixels[x, y] = (r,g,b, 255)

    # Save the modified image
    _image.save("../public/dots/dot-%s.png" % color)
