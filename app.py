import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, request, jsonify
from celery import Celery
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

# Configure Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Define the Celery task
@celery.task
def create_graph(graph_type, nodes, edges):
    G = nx.Graph() if graph_type == "undirected" else nx.DiGraph()

    nodes = [int(node) for node in nodes.split(",")]
    G.add_nodes_from(nodes)

    edges = [tuple(map(int, edge.split())) for edge in edges.split(",")]
    G.add_edges_from(edges)

    plt.figure(figsize=(8, 8))
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, node_size=500, node_color="orange", font_size=12, font_color="black")

    # Save the image to a BytesIO buffer
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    # Encode the image as base64 and convert it to a data URL
    img_data = base64.b64encode(img_buffer.read()).decode()
    img_url = f'data:image/png;base64,{img_data}'

    plt.close()
    return img_url

# Define a route to render the HTML form
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create", methods=["POST"])
def create():
    graph_type = request.form.get("graph_type")
    nodes = request.form.get("nodes")
    edges = request.form.get("edges")

    # Create the graph without Celery (for testing)
    img_url = create_graph(graph_type, nodes, edges)

    # Return the image URL as JSON response
    response_data = {"img_url": img_url}
    return jsonify(response_data)


if __name__ == "__main__":
    app.run(debug=True)
