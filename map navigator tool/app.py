from flask import Flask, render_template, request
import folium
import networkx as nx
import math

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    try:
        # Get the start and end coordinates from the form
        start_lat = float(request.form['start_lat'])
        start_lon = float(request.form['start_lon'])
        end_lat = float(request.form['end_lat'])
        end_lon = float(request.form['end_lon'])

        # Parse the additional locations (if any)
        locations_str = request.form['locations']
        locations = []
        if locations_str:
            for line in locations_str.splitlines():
                if line.strip():
                    lat, lon = map(float, line.strip().split(','))
                    locations.append((lat, lon))

        G = nx.Graph()
        G.add_node("Start", pos=(start_lat, start_lon))
        G.add_node("End", pos=(end_lat, end_lon))

        location_names = []
        for idx, loc in enumerate(locations):
            location_name = f"Location {idx + 1}"
            location_names.append(location_name)
            G.add_node(location_name, pos=loc)
        for node1 in G.nodes:
            for node2 in G.nodes:
                if node1 != node2 and not G.has_edge(node1, node2):
                    dist = calculate_distance(G.nodes[node1]['pos'], G.nodes[node2]['pos'])
                    G.add_edge(node1, node2, weight=dist)
        folium_map = folium.Map(location=[start_lat, start_lon], zoom_start=5, tiles='OpenStreetMap')
        for node in G.nodes:
            folium.Marker(G.nodes[node]['pos'], popup=node).add_to(folium_map)

        for edge in G.edges(data=True):
            start_pos = G.nodes[edge[0]]['pos']
            end_pos = G.nodes[edge[1]]['pos']
            folium.PolyLine([start_pos, end_pos], color="blue", weight=1, opacity=0.5).add_to(folium_map)

        path_nodes = ["Start"] + location_names + ["End"]
        full_path = []
        total_distance = 0.0

        for i in range(len(path_nodes) - 1):
            start_node = path_nodes[i]
            end_node = path_nodes[i + 1]
            path_segment = nx.dijkstra_path(G, start_node, end_node, weight='weight')
            segment_distance = nx.dijkstra_path_length(G, start_node, end_node, weight='weight')

            full_path.extend(path_segment[:-1])
            total_distance += segment_distance

        full_path.append(path_nodes[-1])


        for i in range(len(full_path) - 1):
            start_pos = G.nodes[full_path[i]]['pos']
            end_pos = G.nodes[full_path[i + 1]]['pos']
            folium.PolyLine([start_pos, end_pos], color="red", weight=2.5, opacity=1).add_to(folium_map)


        path_info = []
        path_summary = []
        for i in range(len(full_path) - 1):
            start_node = full_path[i]
            end_node = full_path[i + 1]
            distance = G[start_node][end_node]['weight']
            path_info.append({"start": start_node, "end": end_node, "distance": distance})
            path_summary.append(f"{start_node} -> {end_node}: {distance:.3f} km")

        path_summary_str = " -> ".join(path_summary)

        return render_template('result.html', map=folium_map._repr_html_(), path_info=path_info,
                               total_distance=total_distance,
                               start_location="Start", end_location="End",
                               start_to_end_distance=total_distance,
                               path_summary=path_summary_str)

    except Exception as e:
        return str(e), 400

def calculate_distance(pos1, pos2):
    lat1, lon1 = pos1
    lat2, lon2 = pos2
    radius = 6371


    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    # Apply Haversine formula
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = radius * c

    return distance

if __name__ == '__main__':
    app.run(debug=True)
